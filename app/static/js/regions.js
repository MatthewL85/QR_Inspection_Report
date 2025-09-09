/* regions.js — shared country→region dropdown + defaults (v1.0.3) */
(function (global) {
  function countryToCode(name) {
    if (!name) return null;
    const n = ('' + name).toLowerCase().trim();
    const map = {
      // Core EU
      austria: 'AT', belgium: 'BE', bulgaria: 'BG', croatia: 'HR', cyprus: 'CY', 'czech republic': 'CZ', czechia: 'CZ',
      denmark: 'DK', estonia: 'EE', finland: 'FI', france: 'FR', germany: 'DE', greece: 'GR', hungary: 'HU', ireland: 'IE',
      italy: 'IT', latvia: 'LV', lithuania: 'LT', luxembourg: 'LU', malta: 'MT', netherlands: 'NL', poland: 'PL',
      portugal: 'PT', romania: 'RO', slovakia: 'SK', slovenia: 'SI', spain: 'ES', sweden: 'SE',

      // Wider Europe
      'united kingdom': 'GB', uk: 'GB', 'great britain': 'GB', england: 'GB', scotland: 'GB', wales: 'GB', 'northern ireland': 'GB',
      switzerland: 'CH', norway: 'NO', iceland: 'IS', liechtenstein: 'LI',

      // Other supported
      'united states': 'US', usa: 'US', us: 'US',
      canada: 'CA', australia: 'AU', 'new zealand': 'NZ',
      'united arab emirates': 'AE', uae: 'AE', 'u.a.e': 'AE'
    };
    return map[n] || (n.length === 2 ? n.toUpperCase() : null);
  }

  const REGION_LABELS = {
    US: 'State', CA: 'Province', AE: 'Emirate', AU: 'State/Territory', GB: 'County/Region',
    FR: 'Region', DE: 'State (Bundesland)', IT: 'Region', ES: 'Autonomous Community',
    PT: 'District/Region', NL: 'Province', BE: 'Province/Region', CH: 'Canton', AT: 'State (Bundesland)',
  };
  function regionLabelFor(code) { return REGION_LABELS[code] || 'Region'; }

  // ---- Country defaults (fallback when JURIS_DATA lacks these) ----
  const DEFAULTS = {
    IE: { currency: 'EUR', timezone: 'Europe/Dublin' },
    GB: { currency: 'GBP', timezone: 'Europe/London' },
    FR: { currency: 'EUR', timezone: 'Europe/Paris' },
    DE: { currency: 'EUR', timezone: 'Europe/Berlin' },
    ES: { currency: 'EUR', timezone: 'Europe/Madrid' },
    PT: { currency: 'EUR', timezone: 'Europe/Lisbon' },
    NL: { currency: 'EUR', timezone: 'Europe/Amsterdam' },
    BE: { currency: 'EUR', timezone: 'Europe/Brussels' },
    IT: { currency: 'EUR', timezone: 'Europe/Rome' },
    PL: { currency: 'PLN', timezone: 'Europe/Warsaw' },
    SE: { currency: 'SEK', timezone: 'Europe/Stockholm' },
    FI: { currency: 'EUR', timezone: 'Europe/Helsinki' },
    DK: { currency: 'DKK', timezone: 'Europe/Copenhagen' },
    NO: { currency: 'NOK', timezone: 'Europe/Oslo' },
    IS: { currency: 'ISK', timezone: 'Atlantic/Reykjavik' },
    CH: { currency: 'CHF', timezone: 'Europe/Zurich' },
    AT: { currency: 'EUR', timezone: 'Europe/Vienna' },
    CZ: { currency: 'CZK', timezone: 'Europe/Prague' },
    SK: { currency: 'EUR', timezone: 'Europe/Bratislava' },
    HU: { currency: 'HUF', timezone: 'Europe/Budapest' },
    RO: { currency: 'RON', timezone: 'Europe/Bucharest' },
    BG: { currency: 'BGN', timezone: 'Europe/Sofia' },
    GR: { currency: 'EUR', timezone: 'Europe/Athens' },
    HR: { currency: 'EUR', timezone: 'Europe/Zagreb' },
    SI: { currency: 'EUR', timezone: 'Europe/Ljubljana' },
    LV: { currency: 'EUR', timezone: 'Europe/Riga' },
    LT: { currency: 'EUR', timezone: 'Europe/Vilnius' },
    EE: { currency: 'EUR', timezone: 'Europe/Tallinn' },
    LU: { currency: 'EUR', timezone: 'Europe/Luxembourg' },
    MT: { currency: 'EUR', timezone: 'Europe/Malta' },
    CY: { currency: 'EUR', timezone: 'Asia/Nicosia' },

    US: { currency: 'USD', timezone: 'America/New_York' },
    CA: { currency: 'CAD', timezone: 'America/Toronto' },
    AU: { currency: 'AUD', timezone: 'Australia/Sydney' },
    NZ: { currency: 'NZD', timezone: 'Pacific/Auckland' },
    AE: { currency: 'AED', timezone: 'Asia/Dubai' },
  };
  function defaultsFor(countryNameOrCode) {
    const code = countryToCode(countryNameOrCode);
    return (code && DEFAULTS[code]) ? DEFAULTS[code] : {};
  }

  // ---- Dataset: primary-level subdivisions (EU + UK + EFTA + common non-EU) ----
  const REGIONS = {
    AT: ["Burgenland","Carinthia","Lower Austria","Salzburg","Styria","Tyrol","Upper Austria","Vienna","Vorarlberg"],
    BE: ["Antwerp","Limburg","Flemish Brabant","East Flanders","West Flanders","Hainaut","Liège","Luxembourg","Namur","Walloon Brabant","Brussels-Capital"],
    BG: ["Blagoevgrad","Burgas","Dobrich","Gabrovo","Haskovo","Kardzhali","Kyustendil","Lovech","Montana","Pazardzhik","Pernik","Pleven","Plovdiv","Razgrad","Ruse","Shumen","Silistra","Sliven","Smolyan","Sofia Province","Sofia City","Stara Zagora","Targovishte","Varna","Veliko Tarnovo","Vidin","Vratsa","Yambol"],
    HR: ["Bjelovar-Bilogora","Brod-Posavina","Dubrovnik-Neretva","Istria","Karlovac","Koprivnica-Križevci","Krapina-Zagorje","Lika-Senj","Međimurje","Osijek-Baranja","Požega-Slavonia","Primorje-Gorski Kotar","Šibenik-Knin","Sisak-Moslavina","Split-Dalmatia","Varaždin","Virovitica-Podravina","Vukovar-Syrmia","Zadar","Zagreb County","City of Zagreb"],
    CY: ["Nicosia","Limassol","Larnaca","Paphos","Famagusta"],
    CZ: ["Prague","Central Bohemian","South Bohemian","Plzeň","Karlovy Vary","Ústí nad Labem","Liberec","Hradec Králové","Pardubice","Vysočina","South Moravian","Olomouc","Zlín","Moravian-Silesian"],
    DK: ["Capital Region","Zealand","Southern Denmark","Central Denmark","North Denmark"],
    EE: ["Harju","Hiiu","Ida-Viru","Jõgeva","Järva","Lääne","Lääne-Viru","Põlva","Pärnu","Rapla","Saare","Tartu","Valga","Viljandi","Võru"],
    FI: ["Uusimaa","Southwest Finland","Satakunta","Kanta-Häme","Pirkanmaa","Päijät-Häme","Kymenlaakso","South Karelia","South Savo","North Savo","North Karelia","Central Finland","South Ostrobothnia","Ostrobothnia","Central Ostrobothnia","North Ostrobothnia","Kainuu","Lapland","Åland"],
    FR: ["Auvergne-Rhône-Alpes","Bourgogne-Franche-Comté","Brittany","Centre-Val de Loire","Corsica","Grand Est","Hauts-de-France","Île-de-France","Normandy","Nouvelle-Aquitaine","Occitanie","Pays de la Loire","Provence-Alpes-Côte d'Azur"],
    DE: ["Baden-Württemberg","Bavaria","Berlin","Brandenburg","Bremen","Hamburg","Hesse","Lower Saxony","Mecklenburg-Vorpommern","North Rhine-Westphalia","Rhineland-Palatinate","Saarland","Saxony","Saxony-Anhalt","Schleswig-Holstein","Thuringia"],
    GR: ["Attica","Central Greece","Central Macedonia","Crete","Eastern Macedonia and Thrace","Epirus","Ionian Islands","North Aegean","Peloponnese","South Aegean","Thessaly","Western Greece","Western Macedonia"],
    HU: ["Budapest","Bács-Kiskun","Baranya","Békés","Borsod-Abaúj-Zemplén","Csongrád-Csanád","Fejér","Győr-Moson-Sopron","Hajdú-Bihar","Heves","Jász-Nagykun-Szolnok","Komárom-Esztergom","Nógrád","Pest","Somogy","Szabolcs-Szatmár-Bereg","Tolna","Vas","Veszprém","Zala"],
    IE: ["Carlow","Cavan","Clare","Cork","Donegal","Dublin","Galway","Kerry","Kildare","Kilkenny","Laois","Leitrim","Limerick","Longford","Louth","Mayo","Meath","Monaghan","Offaly","Roscommon","Sligo","Tipperary","Waterford","Westmeath","Wexford","Wicklow"],
    IT: ["Abruzzo","Aosta Valley","Apulia (Puglia)","Basilicata","Calabria","Campania","Emilia-Romagna","Friuli Venezia Giulia","Lazio","Liguria","Lombardy","Marche","Molise","Piedmont","Sardinia","Sicily","Trentino-South Tyrol","Tuscany","Umbria","Veneto"],
    LV: ["Kurzeme","Latgale","Rīga","Vidzeme","Zemgale"],
    LT: ["Alytus","Kaunas","Klaipėda","Marijampolė","Panevėžys","Šiauliai","Tauragė","Telšiai","Utena","Vilnius"],
    LU: ["Capellen","Clervaux","Diekirch","Echternach","Esch-sur-Alzette","Grevenmacher","Luxembourg","Mersch","Redange","Remich","Vianden","Wiltz"],
    MT: ["Northern","Northern Harbour","Southern Harbour","South Eastern","Western","Gozo and Comino"],
    NL: ["Drenthe","Flevoland","Friesland","Gelderland","Groningen","Limburg","North Brabant","North Holland","Overijssel","South Holland","Utrecht","Zeeland"],
    PL: ["Greater Poland","Kuyavian-Pomeranian","Lesser Poland","Łódź","Lower Silesian","Lublin","Lubusz","Masovian","Opole","Podlaskie","Pomeranian","Silesian","Subcarpathian","Świętokrzyskie","Warmian-Masurian","West Pomeranian"],
    PT: ["Aveiro","Beja","Braga","Bragança","Castelo Branco","Coimbra","Évora","Faro","Guarda","Leiria","Lisbon","Portalegre","Porto","Santarém","Setúbal","Viana do Castelo","Vila Real","Viseu","Azores","Madeira"],
    RO: ["Alba","Arad","Argeș","Bacău","Bihor","Bistrița-Năsăud","Botoșani","Brașov","Brăila","Bucharest","Buzău","Călărași","Caraș-Severin","Cluj","Constanța","Covasna","Dâmbovița","Dolj","Galați","Giurgiu","Gorj","Harghita","Hunedoara","Ialomița","Iași","Ilfov","Maramureș","Mehedinți","Mureș","Neamț","Olt","Prahova","Sălaj","Satu Mare","Sibiu","Suceava","Teleorman","Timiș","Tulcea","Vâlcea","Vaslui","Vrancea"],
    SK: ["Bratislava","Trnava","Trenčín","Nitra","Žilina","Banská Bystrica","Prešov","Košice"],
    SI: ["Gorenjska","Goriška","Jugovzhodna Slovenija","Koroška","Notranjsko-kraška","Obalno-kraška","Osrednjeslovenska","Podravska","Pomurska","Posavska","Savinjska","Spodnjeposavska","Zasavska"],
    ES: ["Andalusia","Aragon","Asturias","Balearic Islands","Basque Country","Canary Islands","Cantabria","Castile and León","Castile-La Mancha","Catalonia","Extremadura","Galicia","La Rioja","Madrid","Murcia","Navarre","Valencian Community"],
    SE: ["Blekinge","Dalarna","Gävleborg","Gotland","Halland","Jämtland","Jönköping","Kalmar","Kronoberg","Norrbotten","Örebro","Östergötland","Skåne","Södermanland","Stockholm","Uppsala","Värmland","Västerbotten","Västernorrland","Västmanland","Västra Götaland"],

    GB: ["England","Scotland","Wales","Northern Ireland"],
    CH: ["Aargau","Appenzell Ausserrhoden","Appenzell Innerrhoden","Basel-Landschaft","Basel-Stadt","Bern","Fribourg","Geneva","Glarus","Graubünden","Jura","Lucerne","Neuchâtel","Nidwalden","Obwalden","Schaffhausen","Schwyz","Solothurn","St. Gallen","Thurgau","Ticino","Uri","Valais","Vaud","Zug","Zurich"],
    NO: ["Akershus","Buskerud","Østfold","Innlandet","Møre og Romsdal","Nordland","Rogaland","Troms og Finnmark","Trøndelag","Vestfold","Vestland","Agder","Oslo","Telemark"],
    IS: ["Capital Region","Southern Peninsula","Western Region","Westfjords","Northwest","Northeast","East","South"],
    LI: ["Balzers","Eschen","Gamprin","Mauren","Planken","Ruggell","Schaan","Schellenberg","Triesen","Triesenberg","Vaduz"],

    US: ["Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware","District of Columbia","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming"],
    CA: ["Alberta","British Columbia","Manitoba","New Brunswick","Newfoundland and Labrador","Nova Scotia","Ontario","Prince Edward Island","Quebec","Saskatchewan","Northwest Territories","Nunavut","Yukon"],
    AU: ["New South Wales","Queensland","South Australia","Tasmania","Victoria","Western Australia","Australian Capital Territory","Northern Territory"],
    NZ: ["Auckland","Bay of Plenty","Canterbury","Gisborne","Hawke's Bay","Manawatū-Whanganui","Marlborough","Nelson","Northland","Otago","Southland","Taranaki","Tasman","Waikato","Wellington","West Coast"],
    AE: ["Abu Dhabi","Dubai","Sharjah","Ajman","Umm Al Quwain","Ras Al Khaimah","Fujairah"]
  };

  function init(opts) {
    const { countrySelectorId, hiddenRegionId, selectId, textId, labelId, helpId } = opts || {};
    const countryEl = document.getElementById(countrySelectorId);
    const hiddenEl  = document.getElementById(hiddenRegionId);
    const selEl     = document.getElementById(selectId);
    const txtEl     = document.getElementById(textId);
    const labelEl   = labelId ? document.getElementById(labelId) : null;
    const helpEl    = helpId ? document.getElementById(helpId) : null;

    if (!countryEl || !hiddenEl || !selEl || !txtEl) {
      console.warn('[RegionPicker] Missing element(s).', { countrySelectorId, hiddenRegionId, selectId, textId });
      return;
    }

    function setHidden(v) { hiddenEl.value = v || ''; }
    function setLabel(code) {
      if (!labelEl) return;
      labelEl.textContent = regionLabelFor(code);
      if (!helpEl) return;
      if (code === 'CA') helpEl.textContent = 'Select Province (e.g., ON, QC, BC, AB).';
      else if (code === 'US') helpEl.textContent = 'Select State (e.g., NY, CA, TX).';
      else helpEl.textContent = '';
    }

    function render() {
      const code = countryToCode(countryEl.value);
      const options = code && REGIONS[code] && REGIONS[code].length ? REGIONS[code] : null;
      setLabel(code);

      if (options) {
        selEl.innerHTML = '';
        const ph = document.createElement('option');
        ph.value = ''; ph.textContent = '— Select —';
        selEl.appendChild(ph);
        options.forEach(v => {
          const o = document.createElement('option');
          o.value = v; o.textContent = v;
          selEl.appendChild(o);
        });

        const current = hiddenEl.value || '';
        if (current) {
          const match = Array.from(selEl.options).find(o => (o.value || '') === current);
          selEl.value = match ? current : '';
        } else {
          selEl.value = '';
        }

        selEl.classList.remove('d-none');
        txtEl.classList.add('d-none');
        txtEl.value = '';
        setHidden(selEl.value);
      } else {
        selEl.classList.add('d-none');
        txtEl.classList.remove('d-none');
        if (hiddenEl.value && !txtEl.value) txtEl.value = hiddenEl.value;
      }
    }

    countryEl.addEventListener('change', render);
    countryEl.addEventListener('input', render);
    selEl.addEventListener('change', function () { setHidden(selEl.value); });
    txtEl.addEventListener('input',  function () { setHidden(txtEl.value); });

    render();
  }

  global.RegionPicker = { init, countryToCode, REGIONS, defaultsFor };
})(window);
