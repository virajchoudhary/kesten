const name = process.env.NEXT_PUBLIC_PRODUCT_NAME?.trim() || "Kerquant";

export const brand = {
  name,
  shortName: process.env.NEXT_PUBLIC_PRODUCT_SHORT_NAME?.trim() || name,
  descriptor: "Quantitative research terminal",
};
