import ftplib
import contextlib
import io
import logging

from odoo import fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AtaExchangeSystemFTP(models.Model):
    _inherit = 'ata.exchange.system'

    content_type = fields.Selection(
        selection_add=[
            ('ftp', 'FTP'),
        ],
    )
    
    @contextlib.contextmanager
    def ftp_context(self):
        if self.content_type != 'ftp':
            raise UserError('This method is only applicable for FTP systems')
            
        ftp = None
        try:
            ftp = self.ftp_get_connection()
            yield ftp
        finally:
            if ftp:
                try:
                    ftp.quit()
                except Exception as e:
                    _logger.warning(f"Error closing FTP connection: {str(e)}")

    def ftp_get_connection(self) -> ftplib.FTP:
        try:
            ftp = ftplib.FTP()
            timeout = 30  # Timeout in seconds
            ftp.connect(self.server_address, int(self.server_port), timeout=timeout)
            ftp.login(self.login, self.password)
            _logger.debug(f'Successfully connected to FTP server {self.server_address}')
            return ftp
        except ftplib.all_errors as e:
            error_msg = f'Error connecting to FTP server {self.server_address}: {str(e)}'
            _logger.error(error_msg)
            raise UserError(error_msg)
                    
    def action_test_connection(self):
        """
        Test connection to the FTP server
        """
        if self.content_type != 'ftp':
            super().action_test_connection()
            
        try:
            with self.ftp_context() as ftp:
                welcome_message = ftp.getwelcome()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Result test connection',
                    'message': f'Connection to FTP server established. Server message: {welcome_message}',
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Result test connection',
                    'message': f'Failed to connect to FTP server: {str(e)}',
                    'type': 'danger',
                    'sticky': False,
                }
            }
            
    def ftp_folder_check(self,
        ftp: ftplib.FTP,
        directory_name: str,
        create_if_not_exists: bool = False) -> bool:
        
        try:
            current_dir = ftp.pwd()
                
            try:
                ftp.cwd(f"/{directory_name.strip('/')}")
                ftp.cwd(current_dir)
                return True
            except Exception:
                # Directory doesn't exist
                if create_if_not_exists:
                    return self.ftp_folder_create(ftp, directory_name)
                else:
                    raise ValidationError(f"Directory '{directory_name}' does not exist on FTP server")
        except Exception as e:
            _logger.error(f"Error checking directory {directory_name}: {str(e)}")
            raise
                
    def ftp_folder_create(self,
        ftp: ftplib.FTP,
        directory_name: str) -> bool:

        try:
            ftp.mkd(directory_name)
            _logger.info(f"Successfully created directory: {directory_name}")
            return True
        except Exception as e:
            _logger.error(f"Failed to create directory {directory_name}: {str(e)}")
            raise ValidationError(f"Failed to create directory '{directory_name}' on FTP server: {e}")

    def ftp_move_to_handler_directory(self,
        ftp: ftplib.FTP,
        filename,
        handler_dir: str):
        
        try:
            # Check if handler directory exists, create if not
            self.ftp_folder_check(ftp, handler_dir)
            # Copy file to handler directory
            ftp.rename(filename, f"/{handler_dir.strip('/')}/{filename}")
            _logger.debug(f"Moved file: {filename} to {handler_dir}")
        except Exception as e:
            _logger.error(f"Error moving file {filename} to {handler_dir}: {str(e)}")
            raise

    def ftp_get_files(self,
        ftp: ftplib.FTP,
        extension_list: list[str],
        catalog: str) -> list[str]:

        try:
            ftp.cwd(f"/{catalog.strip('/')}")
            file_list_from_ftp = ftp.nlst()
        
            if not file_list_from_ftp:
                return []

            # Filter out '.' (current directory) and '..' (parent directory) entries
            processed_file_list = [
                filename for filename in file_list_from_ftp if filename not in ('.', '..')
            ]

            # If the list is empty after removing '.' and '..', return empty
            if not processed_file_list:
                return []

            if extension_list:  # If extension_list is provided (not None and not empty)
                # Filter by extensions, case-insensitively
                return [
                    filename for filename in processed_file_list
                    if any(filename.lower().endswith(f".{ext.lower().strip('.')}") for ext in extension_list)
                ]
            else:
                # If extension_list is empty or None, return all files (already filtered for '.' and '..')
                return processed_file_list

        except ftplib.error_perm:
            raise UserError(f"Error accessing directory {catalog}")
        except Exception as e:
            raise UserError(f"Error getting files from directory {catalog}")

    def ftp_download_file_io(self,
        ftp: ftplib.FTP,
        filename: str) -> io.BytesIO:

        try:
            file_data = io.BytesIO()
            ftp.retrbinary(f'RETR {filename}', file_data.write)
            file_data.seek(0)
            _logger.debug(f"Downloaded file: {filename}")
        except Exception as e:
            raise UserError(f"Error downloading file {filename}: {str(e)}")

        return file_data
