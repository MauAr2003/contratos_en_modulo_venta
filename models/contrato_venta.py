from odoo import models, fields, api
from odoo.exceptions import UserError

class ContratoVenta(models.Model):
    _name = 'contrato.venta'
    _description = 'Contrato de Venta'
    _inherit = ['mail.thread','mail.activity.mixin']  # Agrega esto si no lo tienes

    name = fields.Char(string='Contrato', required=True)
    fecha_inicio = fields.Date(string='Del',tracking=True)
    fecha_fin = fields.Date(string='al',tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Cotización Base')
    tipo_contrato = fields.Selection([
        ('abierta', 'Orden Abierta'),
        ('cerrada', 'Orden Cerrada'),
    ], string='Tipo de Contrato', default='abierta' ,tracking=True)
    vendedor = fields.Many2one('res.users', string="Vendedor" , tracking=True)
    partner_id = fields.Many2one('res.partner', string='Cliente')
    currency_id = fields.Many2one('res.currency', string='Moneda')

    referencia = fields.Char(string='Referencia',tracking=True)

    detalle_contrato = fields.One2many(
        comodel_name='contrato.venta.lineas',
        inverse_name='contrato_id',
        string='Detalles'
    )

    sale_order_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='contrato_id',
        string='Órdenes de Venta Generadas'
    )

    sale_order_count = fields.Integer(
        string="Cantidad de Órdenes",
        compute="_compute_sale_order_count",
        store=True
    )

    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        for contrato in self:
            contrato.sale_order_count = len(contrato.sale_order_ids.filtered(lambda o: not o.es_base))

    def action_nueva_orden(self):
        self.ensure_one()

        ordenes_borrador = self.sale_order_ids.filtered(lambda o: o.state == 'draft' and not o.es_base)
        if ordenes_borrador:
            raise UserError("No puedes crear una nueva orden de venta mientras existan órdenes en cotización.")

        order_lines = []
        for linea in self.detalle_contrato:
            
            cantidad_restante = linea.cantidad - linea.ordenado

            if cantidad_restante > 0:
                order_line = (0, 0, {
                    'product_id': linea.product_id.id,
                    'name': linea.descripcion,
                    'product_uom_qty': cantidad_restante,
                    'price_unit': linea.precio,
                    'product_uom': linea.product_id.uom_id.id,
                })
                order_lines.append(order_line)

        if not order_lines:
            raise UserError("Se entregaron todos los productos de este contrato")

        nueva_orden = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'user_id': self.vendedor.id,
            'currency_id': self.currency_id.id,
            'origin': f'Contrato: {self.name}',
            'order_line': order_lines,
            'contrato_id': self.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': nueva_orden.id,
            'target': 'current',
        }

    def action_cerrar(self):
        pass

    def action_cancelar(self):
        pass

    def action_ver_ordenes_venta(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes de Venta del Contrato',
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'domain': [('contrato_id', '=', self.id), ('es_base', '=', False)],
        }


class ContratoVentaLineas(models.Model):
    _name = 'contrato.venta.lineas'
    _description = 'Contrato de venta (lineas)'

    contrato_id = fields.Many2one(
        comodel_name='contrato.venta',
        string='Contrato'
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Producto'
    )

    descripcion = fields.Char(
        string='Descripción',
        related='product_id.name'
    )

    cantidad = fields.Float(
        string='Cantidad'
    )

    # CAMBIO: Convertimos 'ordenado' en campo calculado
    ordenado = fields.Float(
        string='Ordenado',
        compute='_compute_ordenado_entregado',
        store=True
    )

    udm = fields.Char(
        string='UDM',
        related='product_id.uom_id.name'
    )

    precio = fields.Float(
        string='Precio Unitario',
    )

    entregado = fields.Float(
        string='Entregado',
        compute='_compute_ordenado_entregado',
        store=True
    )

    #Método para calcular automáticamente 'ordenado' 
    @api.depends(
        'contrato_id.sale_order_ids.order_line.product_id',
        'contrato_id.sale_order_ids.order_line.product_uom_qty',
        'contrato_id.sale_order_ids.order_line.qty_delivered',
        'contrato_id.sale_order_ids.state',
    )
    def _compute_ordenado_entregado(self):
        for linea in self:
            total_ordenado = 0.0
            total_entregado = 0.0
            for orden in linea.contrato_id.sale_order_ids.filtered(lambda o: not o.es_base and o.state != 'cancel'):
                for orden_line in orden.order_line:
                    if orden_line.product_id == linea.product_id:
                        total_ordenado += orden_line.product_uom_qty
                        total_entregado += orden_line.qty_delivered
            linea.ordenado = total_ordenado
            linea.entregado = total_entregado
