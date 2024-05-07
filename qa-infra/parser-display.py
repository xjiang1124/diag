import sys, os
import pandas as pd
import glob, openpyxl
from rich.console import Console
from rich.table import Table
"""
 'rich' was the only package I could find that allowed left-aligned text together with wrapping long lines.
 Color features are a plus and can style them in the future as needed.
"""

try:
    if not "parse_result" in " ".join(os.listdir()):
        print("No parse_result*.xlsx file created")
        sys.exit(1)
    xslx_file = os.path.join(sys.argv[1], glob.glob("parse_result*.xlsx")[0])
except SystemExit:
    sys.exit(1)
except:
    xslx_file = glob.glob("parse_result*.xlsx")[0]
df = pd.read_excel(xslx_file, engine='openpyxl')
nic_list = df["SN"].tolist()
slot_list = df["Slot"].tolist()
df = df.drop(columns=["Stage", "SN", "Test", "MTP", "EMMC Vendor", "Date", "Rev"]) # reduce text on screen
df = df.set_index("Slot")
column_list = df.columns.tolist()
df = df.T

# build the display
for nic_slot, nic_sn in zip(slot_list, nic_list):
    title = f"[NIC-{nic_slot:02d}] {nic_sn}"
    table = Table(
                  # row_styles = ["","dim"], # alternating row colors
                  show_lines = True        # borders between rows
                  )

    # table.add_column("Field", style="bold white")
    # table.add_column("Value")

    nic_columns = [f"{title} {column_name}" for column_name in column_list[:]] # append SN to each line, for grep
    rows = zip(nic_columns, df[nic_slot].values.tolist())
    rows = [[str(e1) for e1 in row] for row in rows] # sanitize
    for row in rows:
        table.add_row(*row)

    console = Console(width=255) #jobd page size
    console.print(table)
    print("\n")
