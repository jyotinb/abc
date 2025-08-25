#!/bin/bash
# Restore original files from backup
echo "Restoring files from backup..."
cp -r /opt/odoo172/odoo17/agrolt172/greenhouse_framework/backup_20250825_133003/data/* /opt/odoo172/odoo17/agrolt172/greenhouse_framework/data/
echo "Files restored. Restart Odoo to apply changes."
