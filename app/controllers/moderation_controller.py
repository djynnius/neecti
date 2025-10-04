from flask import request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Report, Post, User, Notification
from datetime import datetime

class ModerationController:
    
    @staticmethod
    @login_required
    def create_report():
        """Create a new report for content or user"""
        data = request.get_json()
        
        reason = data.get('reason', '').strip()
        description = data.get('description', '').strip()
        reported_post_id = data.get('post_id')
        reported_user_id = data.get('user_id')
        
        if not reason:
            return jsonify({'error': 'Reason is required'}), 400
        
        if not reported_post_id and not reported_user_id:
            return jsonify({'error': 'Either post_id or user_id is required'}), 400
        
        # Validate reported content exists
        if reported_post_id:
            post = Post.query.get(reported_post_id)
            if not post or post.is_deleted:
                return jsonify({'error': 'Post not found'}), 404
        
        if reported_user_id:
            user = User.query.get(reported_user_id)
            if not user or not user.is_active:
                return jsonify({'error': 'User not found'}), 404
            
            # Prevent self-reporting
            if user.id == current_user.id:
                return jsonify({'error': 'Cannot report yourself'}), 400
        
        # Check if user has already reported this content
        existing_report = Report.query.filter_by(
            reporter_id=current_user.id,
            reported_post_id=reported_post_id,
            reported_user_id=reported_user_id
        ).first()
        
        if existing_report:
            return jsonify({'error': 'You have already reported this content'}), 400
        
        try:
            report = Report(
                reporter_id=current_user.id,
                reported_post_id=reported_post_id,
                reported_user_id=reported_user_id,
                reason=reason,
                description=description
            )
            
            db.session.add(report)
            
            # Mark content as reported
            if reported_post_id:
                post.is_reported = True
            
            db.session.commit()
            
            return jsonify({
                'message': 'Report submitted successfully',
                'report': report.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to submit report'}), 500
    
    @staticmethod
    @login_required
    def get_reports():
        """Get reports for admin review"""
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', 'pending')  # 'pending', 'reviewed', 'resolved', 'dismissed'
        report_type = request.args.get('type')  # 'post', 'user'
        
        query = Report.query
        
        # Filter by status
        if status != 'all':
            query = query.filter_by(status=status)
        
        # Filter by type
        if report_type == 'post':
            query = query.filter(Report.reported_post_id.isnot(None))
        elif report_type == 'user':
            query = query.filter(Report.reported_user_id.isnot(None))
        
        reports = query.order_by(Report.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'reports': [report.to_dict() for report in reports.items],
            'pagination': {
                'page': reports.page,
                'pages': reports.pages,
                'per_page': reports.per_page,
                'total': reports.total,
                'has_next': reports.has_next,
                'has_prev': reports.has_prev
            },
            'filters': {
                'status': status,
                'type': report_type
            }
        }), 200
    
    @staticmethod
    @login_required
    def get_report(report_id):
        """Get specific report details"""
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify({
            'report': report.to_dict()
        }), 200
    
    @staticmethod
    @login_required
    def resolve_report(report_id):
        """Resolve a report"""
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        action = data.get('action', 'resolve')  # 'resolve', 'dismiss'
        notes = data.get('notes', '').strip()
        delete_content = data.get('delete_content', False)
        suspend_user = data.get('suspend_user', False)
        
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        if report.status != 'pending':
            return jsonify({'error': 'Report has already been processed'}), 400
        
        try:
            # Update report status
            if action == 'dismiss':
                report.dismiss(current_user, notes)
            else:
                report.resolve(current_user, notes)
            
            # Take action on reported content if requested
            if delete_content and report.reported_post_id:
                post = Post.query.get(report.reported_post_id)
                if post:
                    post.is_deleted = True
            
            if suspend_user and report.reported_user_id:
                user = User.query.get(report.reported_user_id)
                if user:
                    user.is_active = False
                    # Create notification for suspended user
                    notification = Notification(
                        user_id=user.id,
                        type='system',
                        message='Your account has been suspended due to policy violations.'
                    )
                    db.session.add(notification)
            
            db.session.commit()
            
            return jsonify({
                'message': f'Report {action}d successfully',
                'report': report.to_dict()
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to {action} report'}), 500
    
    @staticmethod
    @login_required
    def get_moderation_stats():
        """Get moderation statistics"""
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        # Count reports by status
        pending_reports = Report.query.filter_by(status='pending').count()
        resolved_reports = Report.query.filter_by(status='resolved').count()
        dismissed_reports = Report.query.filter_by(status='dismissed').count()
        
        # Count reports by type
        post_reports = Report.query.filter(Report.reported_post_id.isnot(None)).count()
        user_reports = Report.query.filter(Report.reported_user_id.isnot(None)).count()
        
        # Count reported content
        reported_posts = Post.query.filter_by(is_reported=True, is_deleted=False).count()
        deleted_posts = Post.query.filter_by(is_deleted=True).count()
        suspended_users = User.query.filter_by(is_active=False).count()
        
        return jsonify({
            'stats': {
                'reports': {
                    'pending': pending_reports,
                    'resolved': resolved_reports,
                    'dismissed': dismissed_reports,
                    'total': pending_reports + resolved_reports + dismissed_reports
                },
                'report_types': {
                    'posts': post_reports,
                    'users': user_reports
                },
                'content': {
                    'reported_posts': reported_posts,
                    'deleted_posts': deleted_posts,
                    'suspended_users': suspended_users
                }
            }
        }), 200
    
    @staticmethod
    @login_required
    def get_reported_content():
        """Get list of reported content for review"""
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        content_type = request.args.get('type', 'posts')  # 'posts', 'users'
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if content_type == 'posts':
            # Get reported posts
            posts = Post.query.filter_by(is_reported=True, is_deleted=False)\
                             .order_by(Post.created_at.desc())\
                             .paginate(page=page, per_page=per_page, error_out=False)
            
            content_data = []
            for post in posts.items:
                post_data = post.to_dict()
                # Add report count
                post_data['report_count'] = Report.query.filter_by(
                    reported_post_id=post.id,
                    status='pending'
                ).count()
                content_data.append(post_data)
            
            return jsonify({
                'posts': content_data,
                'pagination': {
                    'page': posts.page,
                    'pages': posts.pages,
                    'per_page': posts.per_page,
                    'total': posts.total,
                    'has_next': posts.has_next,
                    'has_prev': posts.has_prev
                }
            }), 200
        
        else:  # users
            # Get users with pending reports
            user_ids = db.session.query(Report.reported_user_id)\
                                .filter_by(status='pending')\
                                .filter(Report.reported_user_id.isnot(None))\
                                .distinct().all()
            
            user_ids = [uid[0] for uid in user_ids]
            
            if not user_ids:
                return jsonify({
                    'users': [],
                    'pagination': {'page': 1, 'pages': 0, 'total': 0}
                }), 200
            
            users = User.query.filter(User.id.in_(user_ids))\
                             .paginate(page=page, per_page=per_page, error_out=False)
            
            content_data = []
            for user in users.items:
                user_data = user.to_dict()
                # Add report count
                user_data['report_count'] = Report.query.filter_by(
                    reported_user_id=user.id,
                    status='pending'
                ).count()
                content_data.append(user_data)
            
            return jsonify({
                'users': content_data,
                'pagination': {
                    'page': users.page,
                    'pages': users.pages,
                    'per_page': users.per_page,
                    'total': users.total,
                    'has_next': users.has_next,
                    'has_prev': users.has_prev
                }
            }), 200
    
    @staticmethod
    @login_required
    def bulk_action():
        """Perform bulk actions on reports"""
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        report_ids = data.get('report_ids', [])
        action = data.get('action')  # 'resolve', 'dismiss'
        notes = data.get('notes', '').strip()
        
        if not report_ids or not action:
            return jsonify({'error': 'Report IDs and action are required'}), 400
        
        if action not in ['resolve', 'dismiss']:
            return jsonify({'error': 'Invalid action'}), 400
        
        try:
            reports = Report.query.filter(Report.id.in_(report_ids)).all()
            processed_count = 0
            
            for report in reports:
                if report.status == 'pending':
                    if action == 'dismiss':
                        report.dismiss(current_user, notes)
                    else:
                        report.resolve(current_user, notes)
                    processed_count += 1
            
            db.session.commit()
            
            return jsonify({
                'message': f'Bulk {action} completed',
                'processed_count': processed_count,
                'total_requested': len(report_ids)
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to perform bulk {action}'}), 500
