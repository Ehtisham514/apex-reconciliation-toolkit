"""Verify the published example using the Python standard library."""
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "p": "http://schemas.openxmlformats.org/package/2006/relationships"}


def read_workbook(path):
    """Read the values saved with the workbook, including formula results."""
    sheets = {}
    with ZipFile(path) as archive:
        if any("vbaProject" in p or p.startswith("xl/externalLinks/") for p in archive.namelist()):
            raise ValueError("Unexpected macro or external workbook link")
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(x.itertext()) for x in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        paths = {x.attrib["Id"]: x.attrib["Target"] for x in rels}
        for sheet in ET.fromstring(archive.read("xl/workbook.xml")).findall("m:sheets/m:sheet", NS):
            target = paths[sheet.attrib["{" + NS["r"] + "}id"]]
            target = target.lstrip("/") if target.startswith("/") else "xl/" + target
            cells = {}
            for cell in ET.fromstring(archive.read(target)).findall(".//m:c", NS):
                kind = cell.get("t", "n")
                val = cell.findtext("m:v", namespaces=NS)
                if kind == "e":
                    raise ValueError(f"Excel error in {sheet.get('name')} {cell.get('r')}: {val}")
                if kind == "inlineStr":
                    val = "".join(x.text or "" for x in cell.findall(".//m:t", NS))
                elif val is not None:
                    if kind == "s":
                        val = strings[int(val)]
                    elif kind == "n":
                        val = float(val)
                cells[cell.get("r")] = val
            sheets[sheet.get("name")] = cells
    return sheets


def require(actual, expected, label):
    if actual != expected:
        raise ValueError(f"{label}: expected {expected}, found {actual}")


def verify(path):
    sheets = read_workbook(path)
    filed = sheets["BlackRock filing"]
    for col, close in zip("BCD", [11490, 12779, 8753]):
        value = lambda r: filed[f"{col}{r}"]
        for first, last, subtotal in [(5, 23, 24), (25, 30, 31), (32, 39, 40)]:
            require(sum(value(i) for i in range(first, last + 1)), value(subtotal), f"{col}{subtotal}")
        require(sum(value(i) for i in [24, 31, 40, 41]), value(42), f"{col} change")
        require(value(43) + value(42), value(44), f"{col} closing cash")
        require(value(44), close, f"{col} filed closing amount")
        require([value(i) for i in range(48, 53)], [0] * 5, f"{col} saved controls")
        require(value(53), "TIES", f"{col} control result")

    month = sheets["Cash report"]
    for addr, expected in {"B8": 12000, "B11": 9000, "B15": -4000, "B17": 16000,
                           "B20": 0, "B21": 0, "B22": "RECONCILED"}.items():
        require(month[addr], expected, f"Cash report {addr}")
    register = sheets["Week inputs"]
    plan = sheets["Weekly payments"]
    for delay, expected_minimum in [(0, 4900), (3, -3100)]:
        cash = register["B6"] - register["B7"]
        daily_receipts, daily_payments = [0] * 7, [0] * 7
        for row in range(13, 43):
            if not register.get(f"A{row}"):
                continue
            day = int(register[f"B{row}"] - register["B5"])
            amount = register[f"D{row}"]
            if register[f"C{row}"] == "Payment":
                daily_payments[day] += amount
            else:
                day += delay if register[f"E{row}"] == "Yes" else 0
                if day < 7:
                    daily_receipts[day] += amount
        lows = []
        for i, (payments, receipts) in enumerate(zip(daily_payments, daily_receipts)):
            cash -= payments
            lows.append(cash - register["B8"])
            cash += receipts
            if delay == 0:
                require(plan[f"F{i+8}"], cash, f"Day {i+1} closing cash")
                require(plan[f"G{i+8}"], lows[-1], f"Day {i+1} headroom")
        require(min(lows), expected_minimum, f"Receipt delay {delay} days")
    require(plan["C16"], 4900, "Available now")
    require(sheets["Handover"]["B19"], 13, "Open handover items")
    print("Verified three filed years, monthly tie-outs, seven daily balances, the delayed-receipts case and the handover count.")


if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("Owner-Cash-and-Handover.xlsx")
    verify(path)
