
document.addEventListener("DOMContentLoaded", function () {
  const countrySelect = document.getElementById("countrySelect");
  const clientTypeSelect = document.getElementById("clientTypeSelect");
  const currencyField = document.getElementById("currencyField");
  const legalBasisField = document.getElementById("legalBasisField");
  const vatFieldGroup = document.getElementById("vatFieldGroup");
  const taxFieldGroup = document.getElementById("taxFieldGroup");
  const regionSelect = document.getElementById("regionSelect");
  const timezoneSelect = document.getElementById("timezoneSelect");
  const ownershipTypeSelect = document.getElementById("ownershipTypeSelect");

  // Existing country data for client types, currency, etc.
  const countryData = {
    "Ireland": {
      currency: "EUR",
      clientTypes: ["Owner Management Company", "Commercial Property"],
      legalBasis: "MUD Act 2011",
      regions: ["Leinster", "Munster", "Connacht", "Ulster"],
      timezones: ["Europe/Dublin"],
      ownershipTypes: ["Freehold", "Leasehold"]
    },
    "UK": {
      currency: "GBP",
      clientTypes: ["Resident Management Company", "Right to Manage Company", "Commercial Property"],
      legalBasis: "Leasehold-based, Companies Act",
      regions: ["England", "Scotland", "Wales", "Northern Ireland"],
      timezones: ["Europe/London"],
      ownershipTypes: ["Freehold", "Leasehold", "Share of Freehold"]
    },
    "USA": {
      currency: "USD",
      clientTypes: ["Homeowners Association", "Condominium Owners Association", "Commercial Property"],
      legalBasis: "State-specific laws",
      regions: ["California", "Texas", "New York", "Florida", "Illinois"],
      timezones: ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"],
      ownershipTypes: ["Fee Simple", "Condominium", "Co-op"]
    },
    "Canada": {
      currency: "CAD",
      clientTypes: ["Condominium Corporation", "Strata Corporation", "Commercial Property"],
      legalBasis: "Provincial condominium acts",
      regions: ["Ontario", "British Columbia", "Alberta", "Quebec", "Nova Scotia"],
      timezones: ["America/Toronto", "America/Vancouver"],
      ownershipTypes: ["Strata Title", "Freehold"]
    },
    "Australia": {
      currency: "AUD",
      clientTypes: ["Strata Scheme", "Owners Corporation", "Commercial Property"],
      legalBasis: "Strata Schemes legislation",
      regions: ["New South Wales", "Victoria", "Queensland", "Western Australia", "South Australia"],
      timezones: ["Australia/Sydney", "Australia/Perth"],
      ownershipTypes: ["Strata Title", "Freehold"]
    },
    "New Zealand": {
      currency: "NZD",
      clientTypes: ["Body Corporate", "Commercial Property"],
      legalBasis: "Unit Titles Act",
      regions: ["Auckland", "Wellington", "Canterbury", "Otago"],
      timezones: ["Pacific/Auckland"],
      ownershipTypes: ["Unit Title", "Freehold"]
    },
    "Singapore": {
      currency: "SGD",
      clientTypes: ["MCST (Management Corporation Strata Title)", "Commercial Property"],
      legalBasis: "BMSMA",
      regions: ["Central", "East", "North", "North-East", "West"],
      timezones: ["Asia/Singapore"],
      ownershipTypes: ["Strata Title", "Leasehold"]
    },
    "Hong Kong": {
      currency: "HKD",
      clientTypes: ["Owners’ Corporation", "Commercial Property"],
      legalBasis: "Building Management Ordinance",
      regions: ["Hong Kong Island", "Kowloon", "New Territories"],
      timezones: ["Asia/Hong_Kong"],
      ownershipTypes: ["Leasehold", "Tenancy"]
    },
    "UAE (Dubai)": {
      currency: "AED",
      clientTypes: ["Owners Association", "Commercial Property"],
      legalBasis: "Dubai JOP Law",
      regions: ["Dubai", "Abu Dhabi", "Sharjah"],
      timezones: ["Asia/Dubai"],
      ownershipTypes: ["Freehold", "Commonhold"]
    }
  };

  // Tax configuration for country and region-level overrides
  const taxConfig = {
    "Ireland": { default: "VAT", regions: {} },
    "UK": { default: "VAT", regions: {} },
    "USA": {
      default: "Tax",
      regions: {
        "California": "Tax",
        "Texas": "Tax",
        "New York": "Tax",
        "Florida": "Tax",
        "Illinois": "Tax"
      }
    },
    "Canada": {
      default: "Tax",
      regions: {
        "Ontario": "Tax",
        "Quebec": "Tax",
        "Alberta": "Tax",
        "British Columbia": "Tax",
        "Nova Scotia": "Tax"
      }
    },
    "Australia": {
      default: "Tax",
      regions: {
        "New South Wales": "Tax",
        "Victoria": "Tax",
        "Queensland": "Tax",
        "Western Australia": "Tax",
        "South Australia": "Tax"
      }
    },
    "New Zealand": { default: "Tax", regions: {} },
    "Singapore": { default: "Tax", regions: {} },
    "Hong Kong": { default: "Tax", regions: {} },
    "UAE (Dubai)": { default: "Tax", regions: {} }
  };

  // Populate client type, regions, timezones, ownership types, currency, and tax fields
  window.updateClientTypeOptions = function () {
    const selectedCountry = countrySelect.value;
    const config = countryData[selectedCountry] || {};

    // Currency
    currencyField.value = config.currency || "";

    // Client Types
    clientTypeSelect.innerHTML = '<option value="">-- Select Client Type --</option>';
    (config.clientTypes || []).forEach(type => {
      const opt = document.createElement("option");
      opt.value = type;
      opt.textContent = type;
      opt.setAttribute("data-legal", config.legalBasis || "");
      clientTypeSelect.appendChild(opt);
    });

    // Regions
    regionSelect.innerHTML = '<option value="">-- Select Region --</option>';
    (config.regions || []).forEach(r => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      regionSelect.appendChild(opt);
    });

    // Timezones
    timezoneSelect.innerHTML = '<option value="">-- Select Timezone --</option>';
    (config.timezones || []).forEach(tz => {
      const opt = document.createElement("option");
      opt.value = tz;
      opt.textContent = tz;
      timezoneSelect.appendChild(opt);
    });

    // Ownership Types
    ownershipTypeSelect.innerHTML = '<option value="">-- Select Ownership Type --</option>';
    (config.ownershipTypes || []).forEach(type => {
      const opt = document.createElement("option");
      opt.value = type;
      opt.textContent = type;
      ownershipTypeSelect.appendChild(opt);
    });

    // Update tax fields based on new country selection
    updateTaxFields();
  };

  window.updateLegalBasis = function () {
    const selectedCountry = countrySelect.value;
    const selectedClientType = clientTypeSelect.value;
    const config = countryData[selectedCountry] || {};
    legalBasisField.value = config.legalBasis || "";
  };

  // Determine VAT vs Tax display based on country and region
  window.updateTaxFields = function () {
    const country = countrySelect.value;
    const region = regionSelect.value;
    if (!country || !taxConfig[country]) {
      vatFieldGroup.style.display = "none";
      taxFieldGroup.style.display = "none";
      return;
    }

    const countryRule = taxConfig[country];
    let effectiveTaxType = countryRule.default;
    if (region && countryRule.regions[region]) {
      effectiveTaxType = countryRule.regions[region];
    }

    if (effectiveTaxType === "VAT") {
      vatFieldGroup.style.display = "block";
      taxFieldGroup.style.display = "none";
    } else {
      vatFieldGroup.style.display = "none";
      taxFieldGroup.style.display = "block";
    }
  };

  // Initialize on load (optional: if you want defaults filled)
  updateClientTypeOptions();

  // Attach event listeners to call tax update when region changes
  regionSelect.addEventListener("change", updateTaxFields);
});
