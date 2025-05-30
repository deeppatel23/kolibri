<template>

  <OnboardingStepBase
    :title="header"
    @continue="handleContinue"
  >
    <!-- TODO: Show "you cannot import from this facility" message -->
    <RadioButtonGroup
      v-if="!loadingNewAddress"
      class="radio-group"
      :items="facilities"
      :currentValue.sync="selectedFacilityId"
      :itemLabel="x => formatNameAndId(x.name, x.id)"
      :itemValue="x => x.id"
      :disabled="formDisabled"
    />

    <label class="select-button-label" for="select-address-button">
      {{ $tr('selectDifferentAddressLabel') }}
    </label>
    <KButton
      id="select-address-button"
      appearance="basic-link"
      :text="$tr('addNewAddressAction')"
      @click="showSelectAddressModal = true"
    />

    <SelectAddressModalGroup
      v-if="showSelectAddressModal"
      @cancel="showSelectAddressModal = false"
      @submit="handleAddressSubmit"
    />
  </OnboardingStepBase>

</template>


<script>

  import commonCoreStrings from 'kolibri.coreVue.mixins.commonCoreStrings';
  import commonSyncElements from 'kolibri.coreVue.mixins.commonSyncElements';
  import { SelectAddressModalGroup, RadioButtonGroup } from 'kolibri.coreVue.componentSets.sync';

  import OnboardingStepBase from '../OnboardingStepBase';

  export default {
    name: 'SelectFacilityForm',
    components: {
      OnboardingStepBase,
      RadioButtonGroup,
      SelectAddressModalGroup,
    },
    inject: ['wizardService'],
    mixins: [commonCoreStrings, commonSyncElements],
    data() {
      return {
        // Need to initialize to non-empty string to fix #7595
        selectedFacilityId: 'selectedFacilityId',
        facilities: [],
        device: null,
        formDisabled: false,
        loadingNewAddress: false,
        showSelectAddressModal: false,
      };
    },
    computed: {
      header() {
        return this.getCommonSyncString('selectFacilityTitle');
      },
      importDeviceId() {
        return this.wizardService._state.context.importDeviceId;
      },
      selectedFacility() {
        return this.facilities.find(f => f.id === this.selectedFacilityId);
      },
    },
    mounted() {
      console.log('ImportAuthentication', this.wizardService.state);
    },
    beforeMount() {
      this.fetchNetworkLocation(this.importDeviceId);
    },
    methods: {
      fetchNetworkLocation(deviceId) {
        this.loadingNewAddress = true;
        return this.fetchNetworkLocationFacilities(deviceId)
          .then(data => {
            this.facilities = [...data.facilities];
            this.device = {
              name: data.device_name,
              id: data.device_id,
              baseurl: data.device_address,
            };
            this.selectedFacilityId = this.facilities[0].id;
            this.loadingNewAddress = false;
          })
          .catch(error => {
            // TODO handle disconnected peers error more gracefully
            this.$store.dispatch('showError', error);
          });
      },
      handleAddressSubmit(address) {
        this.fetchNetworkLocation(address.id).then(() => (this.showSelectAddressModal = false));
      },
      handleContinue() {
        //$emit('click_next', { facility: selectedFacility, device: device })
        console.log(this.wizardService._state);
        console.log(this.wizardService.state);
        this.wizardService.send({
          type: 'CONTINUE',
          value: { selectedFacility: this.selectedFacility, importDevice: this.device },
        });
      },
    },
    $trs: {
      selectDifferentAddressLabel: {
        message: "Don't see your learning facility?",
        context:
          'A label shown above a link that will open a modal to select a different network location from which to select a facility',
      },
      addNewAddressAction: {
        message: 'Add new address',
        context:
          'The text for a link that will open a modal that allows the user to add or select a new address from which to import a facility',
      },
    },
  };

</script>


<style lang="scss" scoped>

  .radio-group {
    margin: 1.5em 0;
  }

  .select-button-label {
    display: block;
    margin: 0 0 1em;
  }

</style>
