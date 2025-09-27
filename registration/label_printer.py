"""
Brother QL-700 Label Printer Integration
For DK-22225 labels (38mm height, variable width)
"""

import subprocess
import tempfile
import os
from django.conf import settings
from .models import LabelSettings, Child
import logging

logger = logging.getLogger(__name__)


class BrotherQL700Printer:
    """Brother QL-700 printer integration for DK-22225 labels"""
    
    def __init__(self, printer_name=None):
        self.printer_name = printer_name or self._get_default_printer_name()
        self.label_settings = LabelSettings.get_settings()
    
    def _get_default_printer_name(self):
        """Get the default printer name from settings"""
        settings = LabelSettings.get_settings()
        return settings.printer_name or "Brother QL-700"
    
    def _create_label_html(self, child_data):
        """Create HTML content for a single label"""
        width = self.label_settings.label_width
        height = self.label_settings.label_height
        font_scale = self.label_settings.font_scale
        
        # Icon visibility
        show_medical = self.label_settings.show_medical_icon
        show_dietary = self.label_settings.show_dietary_icon
        show_photo = self.label_settings.show_photo_icon
        
        # Generate icons HTML
        icons_html = ""
        if show_medical:
            medical_class = "yes" if child_data['medical'] else "no"
            icons_html += f'''
            <div class="icon {medical_class}" title="Medical needs">
                <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
                    <rect x="9" y="3" width="6" height="18" rx="2" fill="currentColor"></rect>
                    <rect x="3" y="9" width="18" height="6" rx="2" fill="currentColor"></rect>
                </svg>
            </div>
            '''
        
        if show_dietary:
            dietary_class = "yes" if child_data['dietary'] else "no"
            icons_html += f'''
            <div class="icon {dietary_class}" title="Dietary needs">
                <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
                    <circle cx="12" cy="12" r="7" fill="currentColor"></circle>
                    <rect x="3" y="3" width="2" height="18" fill="currentColor"></rect>
                    <rect x="19" y="3" width="2" height="18" fill="currentColor"></rect>
                </svg>
            </div>
            '''
        
        if show_photo:
            photo_class = "yes" if child_data['photo'] else "no"
            icons_html += f'''
            <div class="icon {photo_class}" title="Photo consent">
                <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
                    <rect x="3" y="7" width="18" height="12" rx="2" fill="currentColor"></rect>
                    <circle cx="12" cy="13" r="4" fill="white"></circle>
                    <circle cx="12" cy="13" r="2" fill="currentColor"></circle>
                </svg>
            </div>
            '''
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Label</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                }}
                
                .label-card {{
                    width: {width}mm;
                    height: {height}mm;
                    border: 1px solid #000;
                    padding: 0.2cm;
                    box-sizing: border-box;
                    display: flex;
                    align-items: center;
                    page-break-inside: avoid;
                }}
                
                .label-grid {{
                    display: grid;
                    grid-template-columns: 1fr auto;
                    column-gap: 0.2cm;
                    height: 100%;
                    align-items: center;
                    width: 100%;
                }}
                
                .col-left {{
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    min-width: 0;
                }}
                
                .first-name {{
                    font-weight: 700;
                    font-size: {8 * font_scale}mm;
                    line-height: {8 * font_scale}mm;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}
                
                .surname {{
                    color: #666;
                    margin: 1mm 0;
                    text-transform: uppercase;
                    font-size: {6 * font_scale}mm;
                    line-height: {6 * font_scale}mm;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}
                
                .class-name {{
                    font-weight: 700;
                    font-size: {7 * font_scale}mm;
                    line-height: {7 * font_scale}mm;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}
                
                .col-icons {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: {2 * font_scale}mm;
                    justify-content: center;
                    min-width: 24px;
                }}
                
                .icon {{
                    color: #000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                
                .icon.no {{
                    color: #999;
                }}
                
                .icon svg {{
                    width: 24px;
                    height: 24px;
                    flex-shrink: 0;
                }}
            </style>
        </head>
        <body>
            <div class="label-card">
                <div class="label-grid">
                    <div class="col-left">
                        <div class="first-name">{child_data['first_name']}</div>
                        <div class="surname">{child_data['last_name']}</div>
                        <div class="class-name">{child_data['class_display']}</div>
                    </div>
                    <div class="col-icons">
                        {icons_html}
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return html_content
    
    def print_child_label(self, child):
        """Print a label for a single child"""
        try:
            # Prepare child data
            child_data = {
                'first_name': child.first_name,
                'last_name': child.last_name,
                'class_display': child.get_class_short_name(),
                'medical': child.has_medical_needs,
                'dietary': child.has_dietary_needs,
                'photo': child.photo_consent
            }
            
            # Create HTML content
            html_content = self._create_label_html(child_data)
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html_file = f.name
            
            try:
                # Print using system print command
                # This works on Windows with default browser
                if os.name == 'nt':  # Windows
                    # Use Windows print command
                    subprocess.run([
                        'powershell', '-Command',
                        f'Start-Process -FilePath "{temp_html_file}" -Verb Print -WindowStyle Hidden'
                    ], check=True, timeout=30)
                else:  # Linux/Mac
                    # Use lpr or similar command
                    subprocess.run([
                        'lpr', '-P', self.printer_name, temp_html_file
                    ], check=True, timeout=30)
                
                logger.info(f"Successfully printed label for {child.first_name} {child.last_name}")
                return True
                
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout printing label for {child.first_name} {child.last_name}")
                return False
            except subprocess.CalledProcessError as e:
                logger.error(f"Error printing label for {child.first_name} {child.last_name}: {e}")
                return False
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_html_file)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"Unexpected error printing label for {child.first_name} {child.last_name}: {e}")
            return False
    
    def print_multiple_labels(self, children):
        """Print labels for multiple children"""
        results = []
        for child in children:
            success = self.print_child_label(child)
            results.append({
                'child': child,
                'success': success
            })
        return results
    
    def test_printer_connection(self):
        """Test if the printer is available and accessible"""
        try:
            if os.name == 'nt':  # Windows
                # Check if printer exists using wmic
                result = subprocess.run([
                    'wmic', 'printer', 'where', f'name="{self.printer_name}"', 'get', 'name'
                ], capture_output=True, text=True, timeout=10)
                return self.printer_name in result.stdout
            else:  # Linux/Mac
                # Check if printer exists using lpstat
                result = subprocess.run([
                    'lpstat', '-p', self.printer_name
                ], capture_output=True, text=True, timeout=10)
                return result.returncode == 0
        except Exception as e:
            logger.error(f"Error testing printer connection: {e}")
            return False


def print_child_label_on_checkin(child):
    """Convenience function to print a label when a child is checked in"""
    settings = LabelSettings.get_settings()
    
    if not settings.auto_print_on_checkin:
        logger.info("Auto-printing is disabled, skipping label print")
        return False
    
    if not settings.printer_name:
        logger.warning("No printer configured for auto-printing")
        return False
    
    printer = BrotherQL700Printer(settings.printer_name)
    return printer.print_child_label(child)
