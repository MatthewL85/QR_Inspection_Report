/* juris.js — tiny helper to compute effective jurisdiction settings.
   Deep-merge order: country → regions["*"] → regions[regionSlug].
   Returns an object like:
     { name, currency, timezone, regionLabel, gdpr, clientTypes, tax, statutes, notes }
*/
(function (window) {
  const ISO_MAP = {
    "ireland":"IE","ie":"IE",
    "united kingdom":"GB","uk":"GB","great britain":"GB","england":"GB","scotland":"GB","wales":"GB","northern ireland":"GB",
    "france":"FR","germany":"DE","spain":"ES","portugal":"PT","netherlands":"NL","belgium":"BE","italy":"IT","poland":"PL",
    "sweden":"SE","finland":"FI","denmark":"DK","norway":"NO","iceland":"IS","switzerland":"CH","austria":"AT",
    "czech republic":"CZ","czechia":"CZ","slovakia":"SK","hungary":"HU","romania":"RO","bulgaria":"BG","greece":"GR",
    "croatia":"HR","slovenia":"SI","latvia":"LV","lithuania":"LT","estonia":"EE","luxembourg":"LU","malta":"MT","cyprus":"CY",
    "liechtenstein":"LI","united states":"US","usa":"US","us":"US","canada":"CA","australia":"AU","new zealand":"NZ",
    "united arab emirates":"AE","uae":"AE","u.a.e":"AE"
  };

  function toSlug(s) {
    return (s || "")
      .toString()
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }
  function lower(s){ return (s||"").toString().trim().toLowerCase(); }
  function countryKey(codeOrName) {
    if (!codeOrName) return "";
    const k = lower(codeOrName);
    if (k.length === 2) return k.toUpperCase();
    return ISO_MAP[k] || codeOrName.toUpperCase();
  }

  function deepMerge(a, b) {
    const out = Array.isArray(a) ? a.slice() : {...a};
    if (!b) return out;
    Object.keys(b).forEach(k => {
      const sv = b[k], tv = out[k];
      if (sv && typeof sv === "object" && !Array.isArray(sv) && tv && typeof tv === "object" && !Array.isArray(tv)) {
        out[k] = deepMerge(tv, sv);
      } else {
        out[k] = sv;
      }
    });
    return out;
  }

  function effective(data, country, region) {
    if (!data || !data.countries) return {};
    const cKey = countryKey(country);
    const countryNode = data.countries[cKey] || {};
    const wildcard = (countryNode.regions && countryNode.regions["*"]) || {};
    const rKeyLower = lower(region);
    const rKeySlug  = toSlug(region);
    const regionNode = (countryNode.regions && (countryNode.regions[rKeyLower] || countryNode.regions[rKeySlug])) || {};
    const merged = deepMerge(deepMerge(countryNode, wildcard), regionNode);
    if (merged.regions) delete merged.regions;
    return merged;
  }

  window.Juris = { effective, toSlug, countryKey };
})(window);
