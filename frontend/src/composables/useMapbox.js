import { ref, computed } from 'vue';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';
const BASE_GEOCODE_URL = 'https://api.mapbox.com/geocoding/v5/mapbox.places';
const DEFAULT_CENTER = [7.4386, 11.0626]; // Kaduna, Nigeria

export function useMapbox() {
  const isLoading = ref(false);
  const error = ref(null);
  const searchResults = ref([]);
  const selectedLocation = ref(null);

  const hasToken = computed(() => !!MAPBOX_TOKEN);

  const searchAddress = async (query) => {
    if (!query || query.length < 3) {
      searchResults.value = [];
      return [];
    }

    isLoading.value = true;
    error.value = null;

    try {
      if (!MAPBOX_TOKEN) {
        // Return mock results for demo when no token
        searchResults.value = getMockAddresses(query);
        return searchResults.value;
      }

      const encodedQuery = encodeURIComponent(query);
      const url = `${BASE_GEOCODE_URL}/${encodedQuery}.json?access_token=${MAPBOX_TOKEN}&limit=5&country=NG&proximity=7.4386,11.0626`;

      const response = await fetch(url);
      const data = await response.json();

      if (data.features && data.features.length > 0) {
        searchResults.value = data.features.map(feature => ({
          id: feature.id,
          place_name: feature.place_name,
          address: feature.address ? `${feature.address} ${feature.text}` : feature.text,
          city: extractContext(feature, 'place') || extractContext(feature, 'locality'),
          state: extractContext(feature, 'region'),
          coordinates: feature.center, // [lng, lat]
        }));
      } else {
        searchResults.value = [];
      }

      return searchResults.value;
    } catch (err) {
      console.error('Geocoding error:', err);
      error.value = 'Failed to search addresses';
      searchResults.value = getMockAddresses(query);
      return searchResults.value;
    } finally {
      isLoading.value = false;
    }
  };

  const extractContext = (feature, type) => {
    const context = feature.context?.find(c => c.id.startsWith(type));
    return context?.text;
  };

  const selectLocation = (location) => {
    selectedLocation.value = location;
    searchResults.value = [];
  };

  const clearSelection = () => {
    selectedLocation.value = null;
    searchResults.value = [];
  };

  return {
    isLoading,
    error,
    searchResults,
    selectedLocation,
    hasToken,
    defaultCenter: DEFAULT_CENTER,
    searchAddress,
    selectLocation,
    clearSelection,
  };
}

// Mock addresses for demo when no API key
function getMockAddresses(query) {
  const mockAddresses = [
    { place_name: 'Kaduna State, Nigeria', address: 'Kaduna', city: 'Kaduna', state: 'Kaduna', coordinates: [7.4386, 11.0626] },
    { place_name: 'Zaria, Kaduna, Nigeria', address: 'Zaria', city: 'Zaria', state: 'Kaduna', coordinates: [7.7234, 11.1117] },
    { place_name: 'Sabon Gari, Zaria, Kaduna, Nigeria', address: 'Sabon Gari', city: 'Sabon Gari', state: 'Kaduna', coordinates: [7.7500, 11.1333] },
    { place_name: 'Barnawa, Kaduna, Nigeria', address: 'Barnawa', city: 'Kaduna', state: 'Kaduna', coordinates: [7.4539, 10.9931] },
    { place_name: 'GRA Kaduna, Nigeria', address: 'GRA', city: 'Kaduna', state: 'Kaduna', coordinates: [7.4250, 11.0580] },
    { place_name: 'Kafanchan, Kaduna, Nigeria', address: 'Kafanchan', city: 'Kafanchan', state: 'Kaduna', coordinates: [8.3000, 9.4833] },
    { place_name: 'Sabon Gari, Kano, Nigeria', address: 'Sabon Gari', city: 'Kano', state: 'Kano', coordinates: [8.5833, 12.0000] },
  ];

  const lowerQuery = query.toLowerCase();
  return mockAddresses.filter(addr => 
    addr.address.toLowerCase().includes(lowerQuery) ||
    addr.city.toLowerCase().includes(lowerQuery) ||
    addr.state.toLowerCase().includes(lowerQuery)
  );
}

export default useMapbox;