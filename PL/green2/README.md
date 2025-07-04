# Greenhouse Management System

Advanced greenhouse structure management module for Odoo 17.0 with Excel-style component management and automated calculations.

## 🚀 Features

### Excel-Style Interface
- **Editable Tables**: Component management with inline editing like Excel
- **Column Headers**: Name | Required | Nos | Length | Pipe | Size | WT | Total Length | Total Cost
- **Automatic Totals**: Section-wise and grand totals calculated in real-time

### Automated Calculations
- **Structure Dimensions**: Input basic dimensions and get all component quantities calculated automatically
- **Multi-Section Organization**: Components organized into ASC, Frame, Truss, and Lower sections
- **Real-time Updates**: Changes in structure dimensions instantly update all component calculations

### Pipe Management
- **Complete Specifications**: Pipe type, size, wall thickness, weight, and rates
- **Master Data**: Pre-configured pipe types, sizes, and wall thickness options
- **Cost Calculations**: Automatic cost calculations based on specifications

### Professional Reports
- **Clean PDF Output**: Well-formatted reports for clients and internal use
- **Detailed Breakdowns**: Component-wise details with specifications
- **Cost Summaries**: Section totals and grand total

## 📦 Installation

1. Copy the `greenh` folder to your Odoo addons directory
2. Restart Odoo server: `sudo systemctl restart odoo`
3. Go to Odoo > Apps > Update App List
4. Search for "Greenhouse Management System" and install

## 🎯 Usage

1. **Create New Project**: Go to Greenhouse Management > Greenhouse Master
2. **Configure Structure**: Enter dimensions and requirements in configuration tabs
3. **Calculate Components**: Click "Calculate Components" button to auto-generate all component lines
4. **Assign Pipes**: Select pipe specifications for each component in the Excel-style tables
5. **Generate Reports**: Print professional PDF reports with complete breakdowns

## 📊 Component Sections

### ASC (Aerodynamic Side Corridors)
- ASC pipe supports and corridor components
- Automated hockey pipe calculations

### Frame Components
- Column specifications (middle, main, thick)
- Anchor frame calculations

### Truss Components
- Arch components (big/small)
- Bottom chord and support calculations
- Purlin specifications

### Lower Section Components
- Screen systems and roll-up mechanisms
- Cross bracing components
- Gutter systems

## 🔧 Technical Details

- **Platform**: Odoo 17.0
- **Database**: PostgreSQL
- **Programming**: Python 3.8+
- **Frontend**: Odoo Web Client with enhanced tabular views
- **Reports**: QWeb PDF generation

## 📄 License

This module is licensed under LGPL-3.

---

**Created with ❤️ for greenhouse construction professionals**