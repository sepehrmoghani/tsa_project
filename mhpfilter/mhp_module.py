from PyPDF2 import PdfReader
import pandas as pd
import tabula

def read_pdf(input):
    with open(input, 'rb') as file:
        pdf_reader = PdfReader(file)
        total_pages = len(pdf_reader.pages)

    if total_pages < 3:
        raise ValueError("PDF does not have enough pages.")

    pages_to_read = '3-' + str(total_pages)
    dfs = tabula.read_pdf(input, pages=pages_to_read, multiple_tables=True, pandas_options={'dtype': str})

    return dfs

def filter_mhp_rows(df):
    return df[df.apply(lambda row: row.astype(str).str.contains('MHP').any(), axis=1)]

def merge_page_columns(filtered_rows):
    page_columns = [col for col in filtered_rows if col.startswith('Page')]
    filtered_rows['GST($)'] = filtered_rows[page_columns].apply(
        lambda x: ' '.join(x.dropna().astype(str)),
        axis=1
    )
    filtered_rows.drop(columns=page_columns, inplace=True)

def merge_tax_invoice_columns(filtered_rows):
    tax_invoice_cols = [col for col in filtered_rows.columns if col.startswith('Tax Invoice')]
    filtered_rows['Tax Invoice/Statement No'] = filtered_rows[tax_invoice_cols].apply(
        lambda x: ' '.join(x.dropna().astype(str)),
        axis=1
    )

def rename_numeric_columns(filtered_rows):
    for col in filtered_rows.columns:
        if col.isnumeric():
            filtered_rows.rename(columns={col: 'Total Including GST'}, inplace=True)

def brittany_filter(dfs, pdf_input):
    filtered_rows = pd.DataFrame()

    for df in dfs:
        filtered_df = filter_mhp_rows(df)
        filtered_rows = pd.concat([filtered_rows, filtered_df], ignore_index=True)

    merge_page_columns(filtered_rows)
    merge_tax_invoice_columns(filtered_rows)
    rename_numeric_columns(filtered_rows)

    return filtered_rows
