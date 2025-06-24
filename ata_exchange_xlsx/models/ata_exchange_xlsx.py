import logging
import io
import pandas as pd
from pandas._typing import DtypeArg
from typing import TypedDict

from odoo import models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ExcelParseParams(TypedDict):
    """Defines the structure for parameters used in parsing an Excel file."""
    rows_to_skip: int
    column_mapping: dict[str, int]


class AtaExchangeXlsx(models.AbstractModel):
    _name = 'ata.exchange.xlsx'
    _description = 'XLSX Handler'

    def xlsx_parse_data(self,
        file_data: io.BytesIO,
        params: ExcelParseParams,
        filename: str,
        dtype: DtypeArg = {}) -> pd.DataFrame:

        try:
            # Get parsing parameters from the strongly-typed dictionary
            rows_to_skip = params.get('rows_to_skip', 0)
            column_mapping = params.get('column_mapping', {})

            if not column_mapping:
                raise UserError(f"Configuration 'column_mapping' not found for file {filename}")

            cols_to_read_indices = list(column_mapping.values())
            new_col_names = list(column_mapping.keys())

            # Read Excel file into pandas DataFrame
            # The # type: ignore is used on the 'names' parameter line to suppress a persistent
            # false-positive error from the linter. The code is functionally correct.
            df = pd.read_excel(
                file_data,
                engine='openpyxl',
                header=None,
                skiprows=rows_to_skip,
                usecols=cols_to_read_indices,
                names=new_col_names,  # type: ignore
                dtype=dtype,
            )
            
            # Validate that all expected columns are present in the DataFrame
            missing_columns = [col for col in new_col_names if col not in df.columns]
            
            if missing_columns:
                raise UserError(f"Missing required columns in {filename}: {missing_columns}")
                
            _logger.debug(f"Successfully parsed Excel file: {filename}, found {len(df)} rows")

            return df
            
        except Exception as e:
            raise UserError(f"Error parsing Excel file: {filename}: {str(e)}")
