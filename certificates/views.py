
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from channels.models import Channel
from .models import Certificate
from .utils import generate_certificate

@login_required
def certificate_download(request, channel_id):
    channel = Channel.objects.get(id=channel_id)

    cert, created = Certificate.objects.get_or_create(
        user=request.user,
        channel=channel,
        defaults={'pdf': ''}
    )

    if created or not cert.pdf:
        cert = generate_certificate(request.user, channel)

    return redirect(cert.pdf.url)
