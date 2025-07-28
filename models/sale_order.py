from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    contrato_id = fields.Many2one('contrato.venta', string='Contrato', readonly=True)
    show_crear_contrato_button = fields.Boolean(compute='_compute_show_crear_contrato_button')
    es_base = fields.Boolean(string='Es Cotización Base', default=False)
    @api.depends('state')
    def _compute_show_crear_contrato_button(self):
     for order in self:
        order.show_crear_contrato_button = order.state == 'sent' 
    
    def action_crear_contrato(self):
        self.ensure_one()
        if self.state != 'sent':
            raise UserError("Solo puedes crear un contrato desde una cotización enviada.")
        detalle_contrato =[]
        for item in self.order_line:
            documento_partida = {
                'product_id': item.product_id.id,
                'descripcion': item.product_id.description_sale,
                'cantidad': item.product_uom_qty,
                'ordenado': 0.0,
                'entregado': 0.0,
                'udm': item.product_uom.id,
                'precio': item.price_unit,
            }
            detalle_contrato.append([0,0,documento_partida])
            
        
        sequence_obj = self.env['ir.sequence']
        correlativo = sequence_obj.next_by_code('secuencia.contrato.principal')


        contrato = self.env['contrato.venta'].create({
            #'name': f"Contrato de {self.name}",
            'name': correlativo,
            'fecha_inicio': self.date_order, 
            'sale_order_id': self.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'detalle_contrato': detalle_contrato,
            'vendedor': self.user_id.id,
            
            
            
        })
        self.contrato_id = contrato.id #añaade el contrato a la cotizacion
        self.es_base = True #Define si una cotizacion es base 
        self.write({'state': 'cancel'})
        self.message_post(body=f"La cotización fue cancelada por el contrato {contrato.name}.")
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'contrato.venta',
            'view_mode': 'form',
            'res_id': contrato.id,
            'target': 'current',
        }
