# Master list of tracked companies. Edit this one file to add/remove
# constituents — both establish_base.py and fetch_quotes.py import it.
#
# NOTE: changing this list changes the index composition. After editing,
# re-run establish_base.py (Actions tab -> "Establish index base" ->
# Run workflow) to regenerate base.json with the new constituent set,
# otherwise fetch_quotes.py will fail for symbols missing from base.json.

COMPANIES = [
    {"symbol": "CONCOR",      "name": "Container Corp. of India",   "segment": "Rail / Container"},
    {"symbol": "DELHIVERY",   "name": "Delhivery Ltd",               "segment": "E-commerce / 3PL"},
    {"symbol": "BLUEDART",    "name": "Blue Dart Express",           "segment": "Air / Express"},
    {"symbol": "TCIEXP",      "name": "TCI Express",                 "segment": "Surface Express"},
    {"symbol": "TCI",         "name": "Transport Corp. of India",    "segment": "Multimodal"},
    {"symbol": "MAHLOG",      "name": "Mahindra Logistics",          "segment": "3PL / Supply Chain"},
    {"symbol": "VRLLOG",      "name": "VRL Logistics",               "segment": "Surface Freight"},
    {"symbol": "ALLCARGO",    "name": "Allcargo Logistics",          "segment": "Freight Forwarding"},
    {"symbol": "AEGISLOG",    "name": "Aegis Logistics",             "segment": "LPG / Liquid Terminals"},
    {"symbol": "GESHIP",      "name": "Great Eastern Shipping",      "segment": "Shipping"},
    {"symbol": "SCI",         "name": "Shipping Corp. of India",     "segment": "Shipping"},
    {"symbol": "SNOWMAN",     "name": "Snowman Logistics",           "segment": "Cold Chain"},
    {"symbol": "NAVKARCORP",  "name": "Navkar Corporation",          "segment": "ICD / Container"},
    {"symbol": "TVSSCS",      "name": "TVS Supply Chain Solutions",  "segment": "3PL / Supply Chain"},
    {"symbol": "ADANIPORTS",  "name": "Adani Ports & SEZ (APSEZ)",   "segment": "Ports / SEZ"},
    {"symbol": "JSWINFRA",    "name": "JSW Infrastructure",          "segment": "Ports / Terminals"},
]
