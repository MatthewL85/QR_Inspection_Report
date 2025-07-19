
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

  const countryData = {
    "Ireland": {
      currency: "EUR",
      clientTypes: ["Owner Management Company"],
      legalBasis: "MUD Act 2011",
      taxType: "VAT",
      regions: ["Leinster", "Munster", "Connacht", "Ulster"],
      timezones: ["Europe/Dublin"],
      ownershipTypes: ["Freehold", "Leasehold"]
    },
    "UK": {
      currency: "GBP",
      clientTypes: ["Resident Management Company", "Right to Manage Company"],
      legalBasis: "Leasehold-based, Companies Act",
      taxType: "VAT",
      regions: ["England", "Scotland", "Wales", "Northern Ireland"],
      timezones: ["Europe/London"],
      ownershipTypes: ["Leasehold", "Share of Freehold"]
    },
    "USA": {
      currency: "USD",
      clientTypes: ["Homeowners Association", "Condominium Owners Association"],
      legalBasis: "State-specific laws",
      taxType: "Tax",
      regions: ["California", "Texas", "Florida", "New York", "Illinois"],
      timezones: ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"],
      ownershipTypes: ["Fee Simple", "Condominium", "Co-op"]
    },
    "Canada": {
      currency: "CAD",
      clientTypes: ["Condominium Corporation", "Strata Corporation"],
      legalBasis: "Provincial condominium acts",
      taxType: "Tax",
      regions: ["Ontario", "British Columbia", "Alberta", "Quebec"],
      timezones: ["America/Toronto", "America/Vancouver"],
      ownershipTypes: ["Strata Title", "Condo Corporation"]
    },
    "Australia": {
      currency: "AUD",
      clientTypes: ["Strata", "Owners Corporation"],
      legalBasis: "Strata Schemes legislation",
      taxType: "Tax",
      regions: ["New South Wales", "Victoria", "Queensland", "Western Australia"],
      timezones: ["Australia/Sydney", "Australia/Perth"],
      ownershipTypes: ["Strata Title", "Community Title"]
    },
    "New Zealand": {
      currency: "NZD",
      clientTypes: ["Body Corporate"],
      legalBasis: "Unit Titles Act",
      taxType: "Tax",
      regions: ["Auckland", "Wellington", "Canterbury"],
      timezones: ["Pacific/Auckland"],
      ownershipTypes: ["Unit Title"]
    },
    "Singapore": {
      currency: "SGD",
      clientTypes: ["MCST (Management Corporation Strata Title)"],
      legalBasis: "BMSMA",
      taxType: "Tax",
      regions: ["Central", "North", "East", "West", "North-East"],
      timezones: ["Asia/Singapore"],
      ownershipTypes: ["Strata Title"]
    },
    "Hong Kong": {
      currency: "HKD",
      clientTypes: ["Owners’ Corporation"],
      legalBasis: "Building Management Ordinance",
      taxType: "Tax",
      regions: ["Hong Kong Island", "Kowloon", "New Territories"],
      timezones: ["Asia/Hong_Kong"],
      ownershipTypes: ["Leasehold"]
    },
    "UAE (Dubai)": {
      currency: "AED",
      clientTypes: ["Owners Association"],
      legalBasis: "Dubai JOP Law",
      taxType: "Tax",
      regions: ["Dubai", "Abu Dhabi", "Sharjah"],
      timezones: ["Asia/Dubai"],
      ownershipTypes: ["Commonhold", "Freehold"]
    }
  };

  window.fetchCountryConfig = function () {
    const selectedCountry = countrySelect.value;
    const config = countryData[selectedCountry];

    if (!config) return;

    currencyField.value = config.currency;
    legalBasisField.value = config.legalBasis;

    clientTypeSelect.innerHTML = '<option value="">-- Select Client Type --</option>';
    config.clientTypes.forEach(type => {
      const opt = document.createElement("option");
      opt.value = type;
      opt.textContent = type;
      clientTypeSelect.appendChild(opt);
    });

    regionSelect.innerHTML = '<option value="">-- Select Region --</option>';
    config.regions.forEach(r => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      regionSelect.appendChild(opt);
    });

    timezoneSelect.innerHTML = '<option value="">-- Select Timezone --</option>';
    config.timezones.forEach(tz => {
      const opt = document.createElement("option");
      opt.value = tz;
      opt.textContent = tz;
      timezoneSelect.appendChild(opt);
    });

    ownershipTypeSelect.innerHTML = '<option value="">-- Select Ownership Type --</option>';
    config.ownershipTypes.forEach(type => {
      const opt = document.createElement("option");
      opt.value = type;
      opt.textContent = type;
      ownershipTypeSelect.appendChild(opt);
    });

    if (config.taxType === "VAT") {
      vatFieldGroup.style.display = "block";
      taxFieldGroup.style.display = "none";
    } else {
      vatFieldGroup.style.display = "none";
      taxFieldGroup.style.display = "block";
    }
  };

  window.updateLegalBasis = function () {
    const selectedCountry = countrySelect.value;
    const selectedClientType = clientTypeSelect.value;
    const config = countryData[selectedCountry];
    if (!config) return;
    legalBasisField.value = config.legalBasis;
  };
});
