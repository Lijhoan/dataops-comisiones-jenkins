#!/usr/bin/env python3
"""
Cálculo de comisiones - DataOps Jenkins + Docker

Flujo:
1. Lee MES_PROCESO_APP en formato AAAAMM. Si no existe, usa el mes actual.
2. Busca el CSV ComisionEmpleados_V1_<periodo>.csv dentro de /app/data.
3. Lee empleados desde PostgreSQL.
4. Une CSV + BD por empleado_id.
5. Calcula comisión.
6. Genera Excel en /app/output.
7. Opcionalmente envía correo si mail_enabled = true.
"""

from datetime import date
from pathlib import Path
from decimal import Decimal
import json
import os
import sys
import smtplib
from typing import Union

import pandas as pd
import psycopg2

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header


def load_config(path: Union[str, Path, None] = None) -> dict:
    path = Path(path) if path else Path(__file__).with_name("config.json")
    if not path.exists():
        raise FileNotFoundError(f"Config file {path} no encontrado.")
    return json.loads(path.read_text(encoding="utf-8"))


CFG = load_config(os.getenv("CONFIG_FILE"))
DB_CFG = CFG["db"]
SMTP_CFG = CFG.get("smtp", {})
PATHS = CFG["paths"]
REPORT = CFG.get("report", {})


def send_mail(to: str, subj: str, html: str, attachment: Path) -> None:
    msg = MIMEMultipart()
    msg["From"] = SMTP_CFG["sender_email"]
    msg["To"] = to
    msg["Subject"] = str(Header(subj, "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with open(attachment, "rb") as fh:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(fh.read())

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{attachment.name}"'
    )
    msg.attach(part)

    with smtplib.SMTP(SMTP_CFG["server"], SMTP_CFG["port"]) as smtp:
        smtp.starttls()
        smtp.login(SMTP_CFG["user"], SMTP_CFG["password"])
        smtp.send_message(msg)


def main() -> None:
    periodo = os.getenv("MES_PROCESO_APP") or date.today().strftime("%Y%m")

    csv_dir = Path(PATHS.get("csv_dir", "/app/data"))
    output_dir = Path(PATHS.get("output_dir", "/app/output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_file = csv_dir / f"ComisionEmpleados_V1_{periodo}.csv"
    excel_out = output_dir / PATHS.get("excel", "ComisionesCalculadas.xlsx")

    print(f"> Periodo de proceso: {periodo}")
    print(f"> Buscando CSV: {csv_file}")

    if not csv_file.exists():
        raise FileNotFoundError(f"No existe el archivo CSV requerido: {csv_file}")

    csv_df = pd.read_csv(csv_file, sep=";")
    print(f"> Filas leídas desde CSV: {len(csv_df)}")

    with psycopg2.connect(**DB_CFG) as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM rrhh.empleado;")
        db_df = pd.DataFrame(
            cur.fetchall(),
            columns=[c[0] for c in cur.description]
        )

    print(f"> Filas leídas desde PostgreSQL: {len(db_df)}")

    merged = csv_df.merge(db_df, on="empleado_id")
    print(f"> Filas luego del cruce CSV + BD: {len(merged)}")

    num_cols = ["mnt_salario", "Comisión", "mnt_tope_comision"]
    merged[num_cols] = (
        merged[num_cols]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
    )

    merged["comision_calculada"] = merged.apply(
        lambda r: min(
            Decimal(str(r["mnt_salario"])) * Decimal("0.10") + Decimal(str(r["Comisión"])),
            Decimal(str(r["mnt_tope_comision"]))
        ),
        axis=1
    )

    merged["periodo"] = periodo

    merged.to_excel(excel_out, index=False, engine="openpyxl")
    print(f"> Excel generado correctamente: {excel_out}")

    if CFG.get("mail_enabled", False):
        send_mail(
            REPORT["to"],
            REPORT["subject"],
            REPORT["body_html"],
            excel_out
        )
        print("> Correo enviado correctamente.")
    else:
        print("> Envío de correo deshabilitado para ejecución CI/CD.")


if __name__ == "__main__":
    main()
