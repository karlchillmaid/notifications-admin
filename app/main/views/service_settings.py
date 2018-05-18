from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from notifications_python_client.errors import HTTPError
from notifications_utils.field import Field
from notifications_utils.formatters import formatted_list

from app import (
    billing_api_client,
    current_service,
    email_branding_client,
    inbound_number_client,
    organisations_client,
    service_api_client,
    user_api_client,
    zendesk_client,
)
from app.main import main
from app.main.forms import (
    ConfirmPasswordForm,
    FreeSMSAllowance,
    InternationalSMSForm,
    LetterBranding,
    LinkOrganisationsForm,
    OrganisationTypeForm,
    RenameServiceForm,
    RequestToGoLiveForm,
    ServiceEditInboundNumberForm,
    ServiceInboundNumberForm,
    ServiceLetterContactBlockForm,
    ServiceReplyToEmailForm,
    ServiceSetBranding,
    ServiceSmsSenderForm,
    ServiceSwitchLettersForm,
    SMSPrefixForm,
)
from app.utils import (
    AgreementInfo,
    email_safe,
    get_cdn_domain,
    user_has_permissions,
    user_is_platform_admin,
)


# @main.route("/services/<service_id>/service-settings")
# @login_required
# @user_has_permissions('manage_service', 'manage_api_keys')
# def service_settings(service_id):
#     letter_branding_organisations = email_branding_client.get_letter_email_branding()
#     organisation = organisations_client.get_service_organisation(service_id).get('name', None)

#     if current_service['email_branding']:
#         email_branding = email_branding_client.get_email_branding(current_service['email_branding'])['email_branding']
#     else:
#         email_branding = None

#     inbound_number = inbound_number_client.get_inbound_sms_number_for_service(service_id)
#     disp_inbound_number = inbound_number['data'].get('number', '')
#     reply_to_email_addresses = service_api_client.get_reply_to_email_addresses(service_id)
#     reply_to_email_address_count = len(reply_to_email_addresses)
#     default_reply_to_email_address = next(
#         (x['email_address'] for x in reply_to_email_addresses if x['is_default']), "Not set"
#     )
#     letter_contact_details = service_api_client.get_letter_contacts(service_id)
#     letter_contact_details_count = len(letter_contact_details)
#     default_letter_contact_block = next(
#         (Field(x['contact_block'], html='escape') for x in letter_contact_details if x['is_default']), "Not set"
#     )
#     sms_senders = service_api_client.get_sms_senders(service_id)
#     sms_sender_count = len(sms_senders)
#     default_sms_sender = next(
#         (Field(x['sms_sender'], html='escape') for x in sms_senders if x['is_default']), "None"
#     )

#     free_sms_fragment_limit = billing_api_client.get_free_sms_fragment_limit_for_year(service_id)

#     return render_template(
#         'views/service-settings.html',
#         email_branding=email_branding,
#         letter_branding=letter_branding_organisations.get(
#             current_service.get('dvla_organisation', '001')
#         ),
#         can_receive_inbound=('inbound_sms' in current_service['permissions']),
#         inbound_number=disp_inbound_number,
#         default_reply_to_email_address=default_reply_to_email_address,
#         reply_to_email_address_count=reply_to_email_address_count,
#         default_letter_contact_block=default_letter_contact_block,
#         letter_contact_details_count=letter_contact_details_count,
#         default_sms_sender=default_sms_sender,
#         sms_sender_count=sms_sender_count,
#         free_sms_fragment_limit=free_sms_fragment_limit,
#         prefix_sms=current_service['prefix_sms'],
#         organisation=organisation,
#     )


@main.route("/services/<service_id>/service-settings/request-to-go-live")
@login_required
@user_has_permissions('manage_service')
def request_to_go_live(service_id):
    return render_template(
        'views/service-settings/request-to-go-live.html',
        has_team_members=(
            user_api_client.get_count_of_users_with_permission(
                service_id, 'manage_service'
            ) > 1
        ),
        has_templates=(
            service_api_client.count_service_templates(service_id) > 0
        ),
        has_email_templates=(
            service_api_client.count_service_templates(service_id, template_type='email') > 0
        ),
        has_email_reply_to_address=bool(
            service_api_client.get_reply_to_email_addresses(service_id)
        )
    )


@main.route("/services/<service_id>/service-settings/submit-request-to-go-live", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def submit_request_to_go_live(service_id):
    form = RequestToGoLiveForm()

    if form.validate_on_submit():
        zendesk_client.create_ticket(
            subject='Request to go live - {}'.format(current_service['name']),
            message=(
                'On behalf of {} ({})\n'
                '\n---'
                '\nOrganisation type: {}'
                '\nAgreement signed: {}'
                '\nChannel: {}\nStart date: {}\nStart volume: {}'
                '\nPeak volume: {}'
                '\nFeatures: {}'
            ).format(
                current_service['name'],
                url_for('main.service_dashboard', service_id=current_service['id'], _external=True),
                current_service['organisation_type'],
                AgreementInfo.from_current_user().as_human_readable,
                formatted_list(filter(None, (
                    'email' if form.channel_email.data else None,
                    'text messages' if form.channel_sms.data else None,
                    'letters' if form.channel_letter.data else None,
                )), before_each='', after_each=''),
                form.start_date.data,
                form.start_volume.data,
                form.peak_volume.data,
                formatted_list(filter(None, (
                    'one off' if form.method_one_off.data else None,
                    'file upload' if form.method_upload.data else None,
                    'API' if form.method_api.data else None,
                )), before_each='', after_each='')
            ),
            ticket_type=zendesk_client.TYPE_QUESTION,
            user_email=current_user.email_address,
            user_name=current_user.name
        )

        flash('Thanks for your request to go live. We’ll get back to you within one working day.', 'default')
        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template('views/service-settings/submit-request-to-go-live.html', form=form)


@main.route("/services/<service_id>/service-settings/switch-live")
@login_required
@user_is_platform_admin
def service_switch_live(service_id):
    service_api_client.update_service(
        current_service['id'],
        # TODO This limit should be set depending on the agreement signed by
        # with Notify.
        message_limit=250000 if current_service['restricted'] else 50,
        restricted=(not current_service['restricted'])
    )
    return redirect(url_for('.service_settings', service_id=service_id))


@main.route("/services/<service_id>/service-settings/research-mode")
@login_required
@user_is_platform_admin
def service_switch_research_mode(service_id):
    service_api_client.update_service_with_properties(
        service_id,
        {"research_mode": not current_service['research_mode']}
    )
    return redirect(url_for('.service_settings', service_id=service_id))


def switch_service_permissions(service_id, permission, sms_sender=None):

    force_service_permission(
        service_id,
        permission,
        on=permission not in current_service['permissions'],
        sms_sender=sms_sender
    )


def force_service_permission(service_id, permission, on=False, sms_sender=None):

    permissions, permission = set(current_service['permissions']), {permission}

    update_service_permissions(
        service_id,
        permissions | permission if on else permissions - permission,
        sms_sender=sms_sender
    )


def update_service_permissions(service_id, permissions, sms_sender=None):

    current_service['permissions'] = list(permissions)

    data = {'permissions': current_service['permissions']}

    if sms_sender:
        data['sms_sender'] = sms_sender

    service_api_client.update_service_with_properties(service_id, data)


@main.route("/services/<service_id>/service-settings/archive", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def archive_service(service_id):
    if request.method == 'POST':
        service_api_client.archive_service(service_id)
        return redirect(url_for('.service_settings', service_id=service_id))
    else:
        flash('There\'s no way to reverse this! Are you sure you want to archive this service?', 'delete')
        return service_settings(service_id)


@main.route("/services/<service_id>/service-settings/suspend", methods=["GET", "POST"])
@login_required
@user_has_permissions('manage_service')
def suspend_service(service_id):
    if request.method == 'POST':
        service_api_client.suspend_service(service_id)
        return redirect(url_for('.service_settings', service_id=service_id))
    else:
        flash("This will suspend the service and revoke all api keys. Are you sure you want to suspend this service?",
              'suspend')
        return service_settings(service_id)


@main.route("/services/<service_id>/service-settings/resume", methods=["GET", "POST"])
@login_required
@user_has_permissions('manage_service')
def resume_service(service_id):
    if request.method == 'POST':
        service_api_client.resume_service(service_id)
        return redirect(url_for('.service_settings', service_id=service_id))
    else:
        flash("This will resume the service. New api key are required for this service to use the API.", 'resume')
        return service_settings(service_id)


@main.route("/services/<service_id>/service-settings/set-inbound-number", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def service_set_inbound_number(service_id):
    available_inbound_numbers = inbound_number_client.get_available_inbound_sms_numbers()
    service_has_inbound_number = inbound_number_client.get_inbound_sms_number_for_service(service_id)['data'] != {}
    inbound_numbers_value_and_label = [
        (number['id'], number['number']) for number in available_inbound_numbers['data']
    ]
    no_available_numbers = available_inbound_numbers['data'] == []
    form = ServiceInboundNumberForm(
        inbound_number_choices=inbound_numbers_value_and_label
    )
    if form.validate_on_submit():
        service_api_client.add_sms_sender(
            current_service['id'],
            sms_sender=form.inbound_number.data,
            is_default=True,
            inbound_number_id=form.inbound_number.data
        )
        switch_service_permissions(current_service['id'], 'inbound_sms')
        return redirect(url_for('.service_settings', service_id=service_id))
    return render_template(
        'views/service-settings/set-inbound-number.html',
        form=form,
        no_available_numbers=no_available_numbers,
        service_has_inbound_number=service_has_inbound_number
    )


@main.route("/services/<service_id>/service-settings/set-letter-contact-block", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def service_set_letter_contact_block(service_id):

    if 'letter' not in current_service['permissions']:
        abort(403)

    form = ServiceLetterContactBlockForm(letter_contact_block=current_service['letter_contact_block'])
    if form.validate_on_submit():
        service_api_client.update_service(
            current_service['id'],
            letter_contact_block=form.letter_contact_block.data.replace('\r', '') or None
        )
        if request.args.get('from_template'):
            return redirect(
                url_for('.view_template', service_id=service_id, template_id=request.args.get('from_template'))
            )
        return redirect(url_for('.service_settings', service_id=service_id))
    return render_template(
        'views/service-settings/set-letter-contact-block.html',
        form=form
    )
