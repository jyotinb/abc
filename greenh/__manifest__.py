# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2024 ZestyBeanz Technologies.
#    (http://wwww.zbeanztech.com)
#    contact@zbeanztech.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Green',
    'version': '17.0.0.0.2',
    'summary': 'This module ensures .',
    'category':'Tools',
    'website': 'http://www.drkdsinfo.com/',
    'description': """
            This module ensures that accounting entries can only be posted if the corresponding Chart of Accounts is approved.
    """,
    'author': 'drkds',
    'license': 'LGPL-3',
    'currency': 'USD',
    'price': 0.0,
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/green_master_views.xml',
        ],
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}





