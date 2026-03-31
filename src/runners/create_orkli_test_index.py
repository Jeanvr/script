import pandas as pd

from src.core.paths import INDEX_DIR


def main():
    rows = [
        {
            "brand": "orkli",
            "supplier_ref": "E-23758-00",
            "normalized_ref": "E23758",
            "name": 'Conjunto tuerca y manguito para válvulas manuales y termostatizables de sistemas monotubo y bitubo formato monotubo (conexión 1/2")',
            "normalized_name": 'conjunto tuerca y manguito para valvulas manuales y termostatizables de sistemas monotubo y bitubo formato monotubo (conexion 1/2")',
            "category": "radiador",
            "image_url": "",
            "pdf_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
            "source_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
        },
        {
            "brand": "orkli",
            "supplier_ref": "E-23545-00",
            "normalized_ref": "E23545",
            "name": 'Pipa 1/2" (Ref. 52390 52290 52490 52590)',
            "normalized_name": 'pipa 1/2 ref 52390 52290 52490 52590',
            "category": "radiador",
            "image_url": "",
            "pdf_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
            "source_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
        },
        {
            "brand": "orkli",
            "supplier_ref": "E-3259-00",
            "normalized_ref": "E3259",
            "name": 'Pipa 1/2"',
            "normalized_name": 'pipa 1/2',
            "category": "radiador",
            "image_url": "",
            "pdf_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
            "source_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
        },
        {
            "brand": "orkli",
            "supplier_ref": "V-08749-00",
            "normalized_ref": "V08749",
            "name": "Maneta blanca + Tornillo para válvulas monotubo 4V manual",
            "normalized_name": "maneta blanca tornillo para valvulas monotubo 4v manual",
            "category": "radiador",
            "image_url": "",
            "pdf_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
            "source_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
        },
        {
            "brand": "orkli",
            "supplier_ref": "E-25353-00",
            "normalized_ref": "E25353",
            "name": "Maneta+Tapa+Tornillo para válvulas bitubo manuales",
            "normalized_name": "maneta tapa tornillo para valvulas bitubo manuales",
            "category": "radiador",
            "image_url": "",
            "pdf_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
            "source_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
        },
        {
            "brand": "orkli",
            "supplier_ref": "V-05369",
            "normalized_ref": "V05369",
            "name": "Motor 240V",
            "normalized_name": "motor 240v",
            "category": "valvula_zona",
            "image_url": "",
            "pdf_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
            "source_url": "https://www.orkli.com/documents/26715/33991/Orkli%2Btarifa%2Brepuestos%2B2021%2Biraila/deb3b515-a3c0-4fbb-8015-a812a463dc95",
        },
    ]

    df = pd.DataFrame(rows)
    output_path = INDEX_DIR / "orkli_products.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"CSV de prueba guardado en: {output_path}")
    print(df[["supplier_ref", "normalized_ref", "name"]])


if __name__ == "__main__":
    main()