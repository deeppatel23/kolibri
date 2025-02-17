<template>

  <OnboardingStepBase
    dir="auto"
    :title="$attrs.header || $tr('adminAccountCreationHeader')"
    :description="$attrs.description || $tr('adminAccountCreationDescription')"
    :noBackAction="noBackAction"
    @continue="handleContinue"
  >
    <slot name="aboveform"></slot>

    <!-- HACK in Import mode, this slot will be replaced by Password-only form -->
    <!-- VUE3-COMPAT: linter doesn't like that we are injecting "footer" slot from
         inside a slot default
    -->
    <slot name="form">
      <!-- Hiding the fullname and username textboxes, but their values are filled in and presumed
           valid if we're given the user that we're taking credentials for (ie, just entering
           password for admin)
      -->
      <FullNameTextbox
        v-show="!selectedUser"
        ref="fullNameTextbox"
        :value.sync="fullName"
        :isValid.sync="fullNameValid"
        :shouldValidate="formSubmitted"
        :autofocus="true"
        autocomplete="name"
      />

      <UsernameTextbox
        v-show="!selectedUser"
        ref="usernameTextbox"
        :value.sync="username"
        :isValid.sync="usernameValid"
        :shouldValidate="formSubmitted"
        :isUniqueValidator="!selectedUser ? uniqueUsernameValidator : () => true"
      />

      <PasswordTextbox
        ref="passwordTextbox"
        :value.sync="password"
        :isValid.sync="passwordValid"
        :shouldValidate="formSubmitted"
        :showConfirmationInput="!selectedUser"
        autocomplete="new-password"
      />

      <!-- NOTE: Demographic info forms were removed in PR #6053 -->

      <PrivacyLinkAndModal v-if="!hidePrivacyLink" />

    </slot>

    <slot name="footer">
      <div class="reminder">
        <div class="icon">
          <KIcon icon="warning" />
        </div>
        <p class="text">
          {{ coreString('rememberThisAccountInformation') }}
        </p>
      </div>
    </slot>
  </OnboardingStepBase>

</template>


<script>

  import every from 'lodash/every';
  import commonCoreStrings from 'kolibri.coreVue.mixins.commonCoreStrings';
  import FullNameTextbox from 'kolibri.coreVue.components.FullNameTextbox';
  import UsernameTextbox from 'kolibri.coreVue.components.UsernameTextbox';
  import PasswordTextbox from 'kolibri.coreVue.components.PasswordTextbox';
  import PrivacyLinkAndModal from 'kolibri.coreVue.components.PrivacyLinkAndModal';
  import OnboardingStepBase from '../OnboardingStepBase';

  export default {
    name: 'UserCredentialsForm',
    components: {
      OnboardingStepBase,
      FullNameTextbox,
      UsernameTextbox,
      PasswordTextbox,
      PrivacyLinkAndModal,
    },
    mixins: [commonCoreStrings],
    inject: ['wizardService'],
    props: {
      // A passthrough to the onboarding step base to hide "GO BACK" when needed
      noBackAction: {
        type: Boolean,
        default: false,
      },
      uniqueUsernameValidator: {
        type: Function,
        default: null,
      },
      hidePrivacyLink: {
        type: Boolean,
        default: false,
      },
      /**
       * The user given which will prefill the data for fullName and username
       */
      selectedUser: {
        type: Object,
        required: false,
        default: null,
      },
    },
    data() {
      let user;
      if (this.selectedUser) {
        user = this.selectedUser;
      } else {
        user = this.$store.state.onboardingData;
      }
      return {
        fullName: user.full_name,
        fullNameValid: false,
        username: user.username,
        usernameValid: false,
        password: '',
        passwordValid: false,
        formSubmitted: false,
      };
    },
    computed: {
      formIsValid() {
        if (this.selectedUser) {
          return this.passwordValid;
        } else {
          return every([this.usernameValid, this.fullNameValid, this.passwordValid]);
        }
      },
    },
    watch: {
      selectedUser(user) {
        // user will be null unless an existing user is selected
        if (user) {
          this.fullName = user.full_name;
          this.username = user.username;
        } else {
          // We should clear the form because this is where the user creates a new superuser
          this.fullName = '';
          this.username = '';
        }
        // Always clear the password field on change
        this.$nextTick(() => {
          this.syncOnboardingData();
          this.focusOnInvalidField();
        });
      },
    },
    mounted() {
      this.syncOnboardingData();
    },
    methods: {
      syncOnboardingData() {
        // Set vuex state w/ the form data
        const payload = {
          password: this.password,
          username: this.username,
          full_name: this.fullName,
        };
        this.$store.commit('SET_USER_CREDENTIALS', payload);
      },
      handleContinue() {
        // Here we will do some final handoff from Vuex to the XState machine
        // We syncOnboardingData (to Vuex)
        // Then we will send the data set in Vuex there into the wizard machine's superuser context
        // value.
        // This will ensure that users' selections persist across page reloads as well.
        this.syncOnboardingData();
        if (!this.formIsValid) {
          this.focusOnInvalidField();
          return;
        } else {
          this.wizardService.send({
            type: 'CONTINUE',
            value: this.$store.state.onboardingData.user,
          });
        }
      },
      focusOnInvalidField() {
        this.$nextTick().then(() => {
          if (!this.fullNameValid) {
            this.$refs.fullNameTextbox.focus();
          } else if (!this.usernameValid) {
            this.$refs.usernameTextbox.focus();
          } else if (!this.passwordValid) {
            this.$refs.passwordTextbox.focus();
          }
        });
      },
    },
    $trs: {
      adminAccountCreationHeader: {
        message: 'Create super admin',
        context:
          "The title of the 'Create a super admin account' section. A super admin can manage all the content and all other Kolibri users on the device.",
      },
      adminAccountCreationDescription: {
        message:
          'This account allows you to manage the facility, resources, and user accounts on this device',
        context: "Description of the 'Create super admin account' page.",
      },
    },
  };

</script>


<style lang="scss" scoped>

  .reminder {
    display: table;
    max-width: 480px;
    padding-top: 1em;

    .icon {
      display: table-cell;
      width: 5%;
      min-width: 32px;
    }

    .text {
      display: table-cell;
      width: 90%;
      vertical-align: top;
    }
  }

  .select {
    margin: 18px 0 36px;
  }

</style>
