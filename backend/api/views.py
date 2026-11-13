from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from functools import lru_cache
import logging
import os
import threading
import uuid
from rest_framework.response import Response
from rest_framework import status
from .security import (
    LegacyOperatorAPIView,
    bounded_float,
    bounded_int,
    is_safe_legacy_session_id,
    legacy_api_view,
    legacy_error_response,
    normalize_ticker,
    normalize_tickers,
    optional_iso_date,
    parse_bool,
)
from django.http import StreamingHttpResponse

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_ai_services():
    from . import ai_services

    return ai_services


@lru_cache(maxsize=1)
def _get_rl_agent():
    return _load_ai_services().RLPortfolioAgent()


def _invalid_request(request, message="Review the supplied values and try again."):
    return legacy_error_response(
        request,
        "invalid_input",
        message,
        status.HTTP_400_BAD_REQUEST,
    )


def _service_unavailable(request, code, message):
    return legacy_error_response(request, code, message, status.HTTP_503_SERVICE_UNAVAILABLE)


def _valid_chat_message(message):
    if isinstance(message, str):
        return 0 < len(message) <= 4000
    if not isinstance(message, list) or not 1 <= len(message) <= 20:
        return False

    total_length = 0
    for item in message:
        if not isinstance(item, dict):
            return False
        if item.get("role") not in {"system", "user", "assistant"}:
            return False
        content = item.get("content")
        if not isinstance(content, str) or len(content) > 4000:
            return False
        total_length += len(content)
    return total_length <= 16000


def _timed_call(func, timeout_seconds, fallback):
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError:
        future.cancel()
        return fallback
    except Exception:
        return fallback
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


class ChatView(LegacyOperatorAPIView):
    def post(self, request):
        message = request.data.get('message')
        if not _valid_chat_message(message):
            return _invalid_request(request, "Enter a message of up to 4,000 characters.")

        response = _load_ai_services().GroqService.chat(message)
        return Response({'response': response})

class TrendPredictionView(LegacyOperatorAPIView):
    def get(self, request, symbol):
        try:
            symbol = normalize_ticker(symbol)
            target_date = optional_iso_date(request.query_params.get('target_date'))
        except ValueError:
            return _invalid_request(request, "Choose a valid ticker and date.")

        from .models import OptimizedHyperparams
        cached = OptimizedHyperparams.get_valid_cache(symbol)

        services = _load_ai_services()
        if cached:
            prediction = services.TrendPredictor.predict(
                symbol,
                hidden_size        = cached.hidden_size,
                num_layers         = cached.num_layers,
                learning_rate      = cached.learning_rate,
                epochs             = cached.epochs,
                dropout            = cached.dropout,
                seq_len            = cached.seq_len,
                hyperparams_source = 'evolved',
                target_date        = target_date
            )
            prediction['evolved_accuracy'] = cached.directional_accuracy
        else:
            prediction = services.TrendPredictor.predict(symbol, target_date=target_date)

        from .models import SearchedTicker
        SearchedTicker.log(symbol)

        return Response(prediction)

class PortfolioOptimizationView(LegacyOperatorAPIView):
    def post(self, request):
        try:
            tickers = normalize_tickers(request.data.get('tickers', []))
            risk_tolerance = bounded_float(
                request.data.get('risk_tolerance'), 0.0, 1.0, default=0.5
            )
            target_date = optional_iso_date(request.data.get('target_date'))
        except ValueError:
            return _invalid_request(request, "Choose 1 to 20 valid tickers and a risk tolerance from 0 to 1.")

        services = _load_ai_services()
            
        # Auto-queue GA for any ticker without an evolved model
        try:
            from .tasks import queue_ga_for_ticker
            from .models import OptimizedHyperparams
            for ticker in tickers:
                if not OptimizedHyperparams.get_valid_cache(ticker):
                    queue_ga_for_ticker(ticker)
        except Exception:
            pass  # never block the optimization request

        optimization_result = services.PortfolioOptimizer.optimize(
            tickers, risk_tolerance, target_date=target_date
        )
        allocation = optimization_result.get("allocation", {})

        reasoning = _timed_call(
            lambda: services.GroqService.analyze_allocation(
                tickers, allocation, risk_tolerance
            ),
            timeout_seconds=2.5,
            fallback="",
        )

        return Response({
            **optimization_result,
            'reasoning': reasoning
        })

class HPOStatusView(LegacyOperatorAPIView):
    def get(self, request):
        from .models import OptimizedHyperparams
        try:
            symbol = normalize_ticker(request.query_params.get('symbol', 'AAPL'))
        except ValueError:
            return _invalid_request(request, "Choose a valid ticker.")
        cached = OptimizedHyperparams.get_valid_cache(symbol)
        if cached:
            return Response({
                'optimized':            True,
                'symbol':               symbol,
                'directional_accuracy': cached.directional_accuracy,
                'val_mse':              cached.val_mse,
                'hidden_size':          cached.hidden_size,
                'num_layers':           cached.num_layers,
                'learning_rate':        cached.learning_rate,
                'epochs':               cached.epochs,
                'cached_at':            cached.created_at.isoformat()
            })
        return Response({'optimized': False, 'symbol': symbol})

class BLOptimizationView(LegacyOperatorAPIView):
    def post(self, request):
        try:
            tickers = normalize_tickers(request.data.get('tickers', []), minimum=2)
            target_date = optional_iso_date(request.data.get('target_date'))
            risk_tolerance = bounded_float(
                request.data.get('risk_tolerance'), 0.0, 1.0, default=0.5
            )
        except ValueError:
            return _invalid_request(
                request,
                "Provide 2 to 20 valid tickers, a risk tolerance from 0 to 1, and a valid date.",
            )

        try:
            from .bl_optimizer import run_black_litterman
        except ImportError:
            return _service_unavailable(
                request,
                "quant_dependency_unavailable",
                "The legacy optimization dependencies are unavailable.",
            )

        result = run_black_litterman(tickers, risk_tolerance, target_date=target_date)

        if result.get("error"):
            return Response({'error': result["error"]}, status=status.HTTP_400_BAD_REQUEST)

        # Groq explanation
        prompt = f"""
        You are a portfolio manager. Explain the following Black-Litterman
        allocation in plain English in 3-4 sentences.

        Tickers: {tickers}
        Risk tolerance: {risk_tolerance:.2f} (0=conservative, 1=aggressive)

        LSTM-based views (what the AI predicts for each stock):
        {result['view_details']}

        Black-Litterman expected returns after blending with market equilibrium:
        {result['bl_returns']}

        Final allocation:
        {result['allocation']}

        Focus on: why the top weighted stocks got higher allocation,
        how the AI views influenced the result, and what the overall
        portfolio stance is (bullish/defensive/balanced).
        """

        reasoning = _timed_call(
            lambda: _load_ai_services().GroqService.chat(prompt),
            timeout_seconds=3.0,
            fallback="",
        )

        return Response({
            **result,
            'reasoning': reasoning
        })


class BlackLittermanAnalysisView(LegacyOperatorAPIView):
    """
    Full Black-Litterman analysis with user-specified views.
    Implements BL math from scratch with NumPy.
    """
    def post(self, request):
        try:
            tickers = normalize_tickers(request.data.get('tickers', []), minimum=2)
            market_weights = request.data.get('market_weights', {})
            views = request.data.get('views', [])
            tau = bounded_float(request.data.get('tau'), 0.0, 1.0, default=0.05)
            risk_free_rate = bounded_float(
                request.data.get('risk_free_rate'), -1.0, 1.0, default=0.02
            )
            if not isinstance(market_weights, dict) or len(market_weights) > 20:
                raise ValueError("Invalid market weights.")
            if not isinstance(views, list) or not 1 <= len(views) <= 20:
                raise ValueError("Invalid view list.")
        except ValueError:
            return _invalid_request(
                request,
                "Provide valid weights, 2 to 20 tickers, and 1 to 20 views.",
            )

        from .bl_numpy import run_bl_analysis
        result = run_bl_analysis(tickers, market_weights, views, tau, risk_free_rate)

        if result.get("error"):
            return Response({'error': result["error"]}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)


class SWOTAnalysisView(LegacyOperatorAPIView):
    def post(self, request):
        query = request.data.get('query', '')
        try:
            target_date = optional_iso_date(request.data.get('target_date'))
            if not isinstance(query, str) or not 1 <= len(query.strip()) <= 300:
                raise ValueError("Invalid query.")
        except ValueError:
            return _invalid_request(
                request,
                "Enter a query of up to 300 characters and a valid date.",
            )

        from .swot_service import run_swot_analysis
        result = run_swot_analysis(query, target_date=target_date)

        if isinstance(result, dict) and result.get("error"):
            return Response({'error': result["error"]}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)


# ─────────────────────────────────────────────────────────────────────────────
# RL Ensemble — Train (async) + Progress poll + HPO cache
# ─────────────────────────────────────────────────────────────────────────────

@legacy_api_view(["POST"])
def train_rl_agent(request):
    try:
        tickers = normalize_tickers(request.data.get("tickers", []), minimum=2)
        timesteps = bounded_int(
            request.data.get("timesteps"), 1, 100_000, default=10_000
        )
        use_hpo = parse_bool(request.data.get("use_hpo"), default=True)
        target_date = optional_iso_date(request.data.get("target_date"))
    except ValueError:
        return _invalid_request(
            request,
            "Provide 2 to 20 valid tickers, 1 to 100,000 timesteps, and a valid date.",
        )

    session_id = uuid.uuid4().hex
    try:
        agent = _get_rl_agent()
    except Exception:
        logger.exception("Legacy RL agent could not be initialized.")
        return _service_unavailable(
            request,
            "legacy_research_unavailable",
            "The legacy research service is unavailable.",
        )

    def run_training():
        try:
            agent.train(
                tickers,
                timesteps=timesteps,
                session_id=session_id,
                use_hpo=use_hpo,
                target_date=target_date,
            )
        except Exception:
            logger.exception("Legacy RL training failed for session %s.", session_id)
            progress_file = os.path.join(agent.PROGRESS_DIR, f"{session_id}.json")
            try:
                agent._write_progress(
                    progress_file,
                    0,
                    "error",
                    total_timesteps=timesteps,
                    extra={"error": "Training failed. Review the server log."},
                )
            except Exception:
                logger.exception("Legacy RL failure state could not be recorded.")

    try:
        threading.Thread(target=run_training, daemon=True).start()
    except Exception:
        logger.exception("Legacy RL training could not be scheduled.")
        return _service_unavailable(
            request,
            "legacy_research_unavailable",
            "The legacy research service is unavailable.",
        )
    return Response(
        {
            "status": "started",
            "session_id": session_id,
            "hpo_enabled": use_hpo and timesteps >= agent.HPO_MIN_TIMESTEPS,
        },
        status=status.HTTP_202_ACCEPTED,
    )


@legacy_api_view(["GET"], throttle_scope="legacy_read")
def rl_progress(request, session_id):
    if not is_safe_legacy_session_id(session_id):
        return legacy_error_response(
            request, "not_found", "Training session not found.", status.HTTP_404_NOT_FOUND
        )
    try:
        return Response(_get_rl_agent().get_progress(session_id))
    except Exception:
        logger.exception("Legacy RL progress could not be read.")
        return _service_unavailable(
            request,
            "legacy_research_unavailable",
            "Training progress is unavailable.",
        )


@legacy_api_view(["GET"], throttle_scope="legacy_read")
def rl_hpo_cache_status(request):
    try:
        ticker_query = request.query_params.get("tickers", "")
        if len(ticker_query) > 420:
            raise ValueError("Ticker list too long.")
        tickers = normalize_tickers(
            [ticker for ticker in ticker_query.split(",") if ticker.strip()],
            minimum=2,
        )
        agent = _get_rl_agent()
        cached = agent._load_hpo_cache(tickers)
        if cached:
            return Response(
                {
                    "cached": True,
                    "ticker_hash": agent._ticker_hash_for_response(tickers),
                    "agents_evolved": list(cached.keys()),
                    "evolved_hyperparams": cached,
                }
            )
        return Response({"cached": False, "tickers": tickers})
    except ValueError:
        return _invalid_request(request, "Provide 2 to 20 valid tickers.")
    except Exception:
        logger.exception("Legacy HPO cache status could not be read.")
        return _service_unavailable(
            request,
            "legacy_research_unavailable",
            "Research cache status is unavailable.",
        )


@legacy_api_view(["DELETE"])
def rl_hpo_cache_clear(request):
    try:
        tickers = normalize_tickers(request.data.get("tickers", []), minimum=2)
        agent = _get_rl_agent()
        import os as _os
        path = agent._hpo_cache_path(tickers)
        if _os.path.exists(path):
            _os.remove(path)
            return Response({"status": "cleared", "tickers": tickers})
        return Response({"status": "no_cache", "tickers": tickers})
    except ValueError:
        return _invalid_request(request, "Provide 2 to 20 valid tickers.")
    except Exception:
        logger.exception("Legacy HPO cache could not be cleared.")
        return _service_unavailable(
            request,
            "legacy_research_unavailable",
            "Research cache could not be updated.",
        )


@legacy_api_view(["GET"])
def stream_evolution(request):
    try:
        symbol = normalize_ticker(request.query_params.get("symbol", "AAPL"))
        pop_size = bounded_int(request.query_params.get("pop_size"), 2, 50, default=5)
        generations = bounded_int(
            request.query_params.get("generations"), 1, 25, default=5
        )
        mutation_rate = bounded_float(
            request.query_params.get("mutation_rate"), 0.0, 1.0, default=0.2
        )
        target_date = optional_iso_date(request.query_params.get("target_date"))
    except ValueError:
        return _invalid_request(
            request,
            "Choose a valid ticker, a valid date, and bounded evolution settings.",
        )

    from .evolution import evolutionary_hpo_generator
    return StreamingHttpResponse(
        evolutionary_hpo_generator(
            symbol=symbol,
            pop_size=pop_size,
            generations=generations,
            mutation_rate=mutation_rate,
            target_date=target_date
        ),
        content_type='application/x-ndjson'
    )

class BacktestPredictionView(LegacyOperatorAPIView):
    def get(self, request, symbol):
        try:
            symbol = normalize_ticker(symbol)
            past_date = optional_iso_date(request.query_params.get("past_date"))
            if past_date is None:
                raise ValueError("A past date is required.")
            force_retrain = parse_bool(
                request.query_params.get("force_retrain", "false"), default=False
            )
        except ValueError:
            return _invalid_request(request, "Choose a valid ticker, date, and force-retrain value.")

        result = _load_ai_services().TrendPredictor.run_backtest(
            symbol, past_date, force_retrain=force_retrain
        )
        if isinstance(result, dict) and "error" in result:
            return _invalid_request(request, "The requested backtest could not be completed.")

        return Response(result)


class ClassicalBacktestView(LegacyOperatorAPIView):
    """
    GET /api/backtest-classical/<symbol>/
    Query params:
      past_date (required, YYYY-MM-DD)

    Runs ARIMA + GARCH backtesting strictly on data before past_date,
    evaluates on data after. Returns results in the same base shape as
    BacktestPredictionView plus confidence interval arrays.
    """
    def get(self, request, symbol):
        try:
            symbol = normalize_ticker(symbol)
            past_date = optional_iso_date(request.query_params.get("past_date"))
            if past_date is None:
                raise ValueError("A past date is required.")
        except ValueError:
            return _invalid_request(request, "Choose a valid ticker and past date.")

        try:
            from .classical_models import ClassicalForecaster

            forecaster = ClassicalForecaster(symbol=symbol, past_date=past_date)
            result = forecaster.run_classical_backtest()
            return Response(result)
        except ValueError:
            return _invalid_request(request, "The requested backtest inputs are invalid.")
        except Exception:
            logger.exception("Legacy classical backtest failed.")
            return _service_unavailable(
                request,
                "legacy_research_unavailable",
                "The classical backtest is unavailable.",
            )
