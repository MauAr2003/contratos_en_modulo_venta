
{
    "name": "Contratos en Cotizacion",
    "version": "1.0",
    "category": "Sales",
    "summary": "Generar un contrato basado en una cotización enviada",
    "author": "Corpotek",
    "depends": ["sale"],
    "data": [
        'security/ir.model.access.csv',
        'views/vista_menu_ordenes.xml', #menu y contrato vista
        'views/sale_order_button_crear_contrato.xml', #agregar boton 
        'data/secuencia.xml',
    ],
    "installable": True,
    "application": False
}
