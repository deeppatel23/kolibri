from django.db import transaction
from django.utils.translation import check_for_language
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from kolibri.core.auth.constants.facility_presets import choices
from kolibri.core.auth.models import Facility
from kolibri.core.auth.models import FacilityUser
from kolibri.core.auth.serializers import FacilitySerializer
from kolibri.core.device.models import DevicePermissions
from kolibri.core.device.models import DeviceSettings
from kolibri.core.device.utils import provision_device
from kolibri.core.device.utils import valid_app_key_on_request
from kolibri.plugins.app.utils import GET_OS_USER
from kolibri.plugins.app.utils import interface
from kolibri.utils.filesystem import check_is_directory
from kolibri.utils.filesystem import get_path_permission


class DevicePermissionsSerializer(serializers.ModelSerializer):

    user = serializers.PrimaryKeyRelatedField(queryset=FacilityUser.objects.all())

    class Meta:
        model = DevicePermissions
        fields = ("user", "is_superuser", "can_manage_content")


class NoFacilityFacilityUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityUser
        fields = ("username", "full_name", "password")


class DeviceSerializerMixin(object):
    def validate_language_id(self, language_id):
        """
        Check that the language_id is supported by Kolibri
        """
        if language_id is not None and not check_for_language(language_id):
            raise serializers.ValidationError(_("Language is not supported by Kolibri"))
        return language_id


class DeviceProvisionSerializer(DeviceSerializerMixin, serializers.Serializer):
    facility = FacilitySerializer(required=False, allow_null=True)
    facility_id = serializers.CharField(max_length=50, required=False, allow_null=True)
    preset = serializers.ChoiceField(choices=choices)
    superuser = NoFacilityFacilityUserSerializer(required=False)
    language_id = serializers.CharField(max_length=15)
    device_name = serializers.CharField(max_length=50, allow_null=True)
    settings = serializers.JSONField()
    allow_guest_access = serializers.BooleanField(allow_null=True)
    is_provisioned = serializers.BooleanField(default=True)

    class Meta:
        fields = (
            "facility",
            "facility_id",
            "superuser",
            "language_id",
            "settings",
            "device_name",
            "allow_guest_access",
            "is_provisioned",
            "superuser",
        )

    def validate(self, data):
        if (
            "superuser" not in data
            and GET_OS_USER in interface
            and "request" in self.context
            and valid_app_key_on_request(self.context["request"])
        ):
            data["os_user"] = True
        elif "superuser" not in data:
            raise serializers.ValidationError("Superuser is required for provisioning")

        has_facility = "facility" in data
        has_facility_id = "facility_id" in data

        if (has_facility and has_facility_id) or (
            not has_facility and not has_facility_id
        ):
            raise serializers.ValidationError(
                "Please provide one of `facility` or `facility_id`; but not both."
            )

        return data

    def create(self, validated_data):
        """
        Endpoint for initial setup of a device.
        Expects a value for:
        default language - the default language of this Kolibri device
        facility - the required fields for setting up a facility
        facilitydataset - facility configuration options
        superuser - the required fields for a facilityuser who will be set as the super user for this device
        """
        with transaction.atomic():
            if validated_data.get("facility"):
                facility_data = validated_data.pop("facility")
                facility_id = None
            else:
                facility_id = validated_data.pop("facility_id")
                facility_data = None

            if facility_id:
                # We've already imported the facility to the device before provisioning
                facility = Facility.objects.get(pk=facility_id)
                preset = facility.dataset.preset
            else:
                facility = Facility.objects.create(**facility_data)
                preset = validated_data.pop("preset")
                facility.dataset.preset = preset
                facility.dataset.reset_to_default_settings(preset)

            custom_settings = validated_data.pop("settings")

            if "on_my_own_setup" in custom_settings:
                facility.on_my_own_setup = custom_settings.pop("on_my_own_setup")

            # overwrite the settings in dataset_data with validated_data.settings
            for key, value in custom_settings.items():
                if value is not None:
                    setattr(facility.dataset, key, value)
            facility.dataset.save()

            # Create superuser only if the details are present and
            # we are in an app that is equipped to handle this.
            # Note that this requires the app to redirect back to the initialization URL
            # after initial provisioning.
            if not validated_data.get("os_user"):
                # We've imported a facility if the username exists
                try:
                    superuser = FacilityUser.objects.get(
                        username=validated_data["superuser"]["username"]
                    )
                except FacilityUser.DoesNotExist:
                    # Otherwise we make the superuser
                    superuser = FacilityUser.objects.create_superuser(
                        validated_data["superuser"]["username"],
                        validated_data["superuser"]["password"],
                        facility=facility,
                        full_name=validated_data["superuser"].get("full_name"),
                    )
            else:
                superuser = None

            # Create device settings
            language_id = validated_data.pop("language_id")
            allow_guest_access = validated_data.pop("allow_guest_access")

            if allow_guest_access is None:
                allow_guest_access = preset != "formal"

            provision_device(
                device_name=validated_data["device_name"],
                is_provisioned=validated_data["is_provisioned"],
                language_id=language_id,
                default_facility=facility,
                allow_guest_access=allow_guest_access,
            )
            return {
                "facility": facility,
                "preset": preset,
                "superuser": superuser,
                "language_id": language_id,
                "settings": custom_settings,
                "allow_guest_access": allow_guest_access,
            }


class PathListField(serializers.ListField):
    def to_representation(self, data):
        return [
            self.child.to_representation(item)
            for item in data
            if check_is_directory(item)
        ]


class DeviceSettingsSerializer(DeviceSerializerMixin, serializers.ModelSerializer):

    extra_settings = serializers.JSONField(required=False)
    primary_storage_location = serializers.CharField(required=False)
    secondary_storage_locations = PathListField(
        child=serializers.CharField(required=False), required=False
    )

    class Meta:
        model = DeviceSettings
        fields = (
            "language_id",
            "landing_page",
            "allow_guest_access",
            "allow_peer_unlisted_channel_import",
            "allow_learner_unassigned_resource_access",
            "allow_other_browsers_to_connect",
            "extra_settings",
            "primary_storage_location",
            "secondary_storage_locations",
        )

    def create(self, validated_data):
        raise serializers.ValidationError("Device settings can only be updated")

    def validate(self, data):
        data = super(DeviceSettingsSerializer, self).validate(data)
        if "primary_storage_location" in data:
            if not check_is_directory(data["primary_storage_location"]):
                raise serializers.ValidationError(
                    {
                        "primary_storage_location": "Primary storage location must be a directory"
                    }
                )
            if not get_path_permission(data["primary_storage_location"]):
                raise serializers.ValidationError(
                    {
                        "primary_storage_location": "Primary storage location must be writable"
                    }
                )

        if "secondary_storage_locations" in data:
            for path in data["secondary_storage_locations"]:
                if path == "" or path is None:
                    continue
                if not check_is_directory(path):
                    raise serializers.ValidationError(
                        {
                            "secondary_storage_locations": "Secondary storage location must be a directory"
                        }
                    )
        return data
