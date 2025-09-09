@super_admin_bp.route('/work-orders', endpoint='work_orders')
@super_admin_required
@login_required
def work_orders():
    return render_template('super_admin/work_orders_placeholder.html')  # or similar
