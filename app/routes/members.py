@members_bp.route('/submit-alert', methods=['GET', 'POST'])
@login_required
def submit_alert():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        priority = request.form['priority']
        unit_id = current_user.unit_id
        media_file = request.files.get('media')

        filename = None
        if media_file:
            filename = secure_filename(media_file.filename)
            media_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            media_file.save(media_path)

        new_alert = Alert(
            title=title,
            description=description,
            category=category,
            priority=priority,
            status='Open',
            submitted_by_id=current_user.id,
            unit_id=unit_id,
            client_id=current_user.client_id,
            created_by=current_user.full_name
        )
        db.session.add(new_alert)
        db.session.commit()
        flash('Your issue has been submitted.', 'success')
        return redirect(url_for('members.view_alerts'))

    return render_template('members/submit_alert.html')

@members_bp.route('/my-alerts')
@login_required
def view_alerts():
    alerts = Alert.query.filter_by(submitted_by_id=current_user.id).order_by(Alert.date_created.desc()).all()
    return render_template('members/my_alerts.html', alerts=alerts)

@members_bp.route('/upcoming-meetings')
@login_required
def upcoming_meetings():
    meetings = BoardMeeting.query.filter(
        BoardMeeting.meeting_date >= datetime.utcnow()
    ).order_by(BoardMeeting.meeting_date).all()

    return render_template('members/upcoming_meetings.html', meetings=meetings)
