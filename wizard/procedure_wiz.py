from datetime import timedelta, date, datetime

__author__ = 'tbri'
from osv import osv,fields


class ProcedureReadOnly(osv.TransientModel):
    _name = 'bc_quality.procedure_wizard'

    _inherit = 'bc_quality.procedure'

    def _calc_next_time(self):
        duration = timedelta( days=(10) )
        next_date = date.today() + duration
        return next_date

    def _get_next_time(self, cr, uid, ids, field, arg, context=None):
        assert len(ids) == 1
        result = {}
        for procedure in self.browse(cr, uid, ids, context=context):
            next_date = self._calc_next_time()
            result[procedure.id] = next_date.strftime("%Y-%m-%d")
        return result


POPULERE MED DATA??

eller heller bruke ein av dei andre klassene for å vise....

    def _set_next_time(self, cr, uid, id, name, value, fnct_inv_arg, context):
        print "SET NEXT TIME", name, value
        # 2014-02-23 17:30:00
        dtdt = datetime.strptime( value, '%Y-%m-%d %H:%M:%S').date()
        next_date = self._calc_next_time()

        if dtdt > next_date:
            return False
            #raise ValueError("Can't postpone activities, only framskunde...")

        print dtdt, next_date, dtdt-next_date
        return True

    _columns = {
        'next_time' : fields.function(fnct=_get_next_time, fnct_inv=_set_next_time, type='date', string='Next test')
    }
