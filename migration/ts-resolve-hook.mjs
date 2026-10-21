// Lader Node (type-stripping) læse webapp/lib/*.ts uden at ændre dem.
// Filerne importerer "./shared" uden endelse, hvilket Next.js tillader, men Node ikke.
// Hooket prøver kun ".ts" når den almindelige opslag fejler.
export async function resolve(specifier, context, nextResolve) {
  try {
    return await nextResolve(specifier, context);
  } catch (err) {
    const relative = specifier.startsWith("./") || specifier.startsWith("../");
    if (err.code === "ERR_MODULE_NOT_FOUND" && relative && !/\.[cm]?[jt]sx?$/.test(specifier)) {
      return nextResolve(`${specifier}.ts`, context);
    }
    throw err;
  }
}
