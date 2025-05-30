<template>

  <div>
    <OnboardingStepBase
      @back="goToLastStep"
      @continue="goToNextStep"
    >

      <div class="main">
        <component :is="currentComponent" />
      </div>
      <template #footer class="footer">
        {{ currentFooter }}
      </template>
    </OnboardingStepBase>
  </div>

</template>


<script>

  import OnboardingStepBase from './OnboardingStepBase';
  import FacilityPermissionsForm from './onboarding-forms/FacilityPermissionsForm';
  import GuestAccessForm from './onboarding-forms/GuestAccessForm';
  import CreateLearnerAccountForm from './onboarding-forms/CreateLearnerAccountForm';
  import RequirePasswordForLearnersForm from './onboarding-forms/RequirePasswordForLearnersForm';
  import PersonalDataConsentForm from './onboarding-forms/PersonalDataConsentForm';

  const stepToComponentMap = {
    1: FacilityPermissionsForm,
    2: GuestAccessForm,
    3: CreateLearnerAccountForm,
    4: RequirePasswordForLearnersForm,
    5: PersonalDataConsentForm,
  };

  const TOTAL_STEPS = 5;

  // Template for the 'New Facility' workflow, which manages the title
  // and back/forth flow for this group of steps
  export default {
    name: 'CreateFacilitySetup',
    components: {
      OnboardingStepBase,
    },
    inject: ['wizardService'],
    computed: {
      currentComponent() {
        const { step } = this.$route.params;
        return stepToComponentMap[step];
      },
      currentStep() {
        return Number(this.$route.params.step);
      },
      currentFooter() {
        return this.$tr('newFacilityStepTitle', {
          step: this.currentStep,
          total: TOTAL_STEPS,
        });
      },
    },
    methods: {
      goToNextStep() {
        if (this.currentStep < TOTAL_STEPS) {
          this.$router.push({
            params: {
              step: this.currentStep + 1,
            },
          });
        } else if (this.currentStep === TOTAL_STEPS) {
          this.finalizeOnboardingData();
        }
      },
      goToLastStep() {
        if (this.currentStep > 1) {
          this.$router.push({
            params: {
              step: this.currentStep - 1,
            },
          });
        } else if (this.currentStep === 1) {
          this.wizardService.send('BACK');
        }
      },
      finalizeOnboardingData() {
        this.$store.dispatch('provisionDevice');
      },
    },
    $trs: {
      newFacilityStepTitle: {
        message: 'New facility - step {step, number} of {total, number}',
        context:
          'Browser window title that displays to indicate the current step in the setup process for a new facility.',
      },
    },
  };

</script>


<style lang="scss" scoped>

  .main {
    margin: 16px;
  }

  .footer {
    margin-top: 16px;
  }

</style>
