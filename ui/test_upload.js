// [R13] Test script for Cloud Storage proxy POST endpoint
// → needs: proxy-server-running
// → provides: config-upload-test

const testConfig = {
  properties: [
    {
      property_id: "249571600",
      dataset_id: "st-ga4-data:analytics_249571600",
      client_name: "Test Client",
      domain: "example.com",
      conversion_events: "purchase, sign_up",
      notes: "Test property for proxy validation",
      is_configured: true
    }
  ]
};

fetch('http://localhost:5000/api/config/properties', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(testConfig)
})
  .then(res => res.json())
  .then(data => {
    console.log('✅ Upload successful:', data);

    // Now fetch it back to verify
    return fetch('http://localhost:5000/api/config/properties');
  })
  .then(res => res.json())
  .then(data => {
    console.log('✅ Retrieved configuration:', data);
  })
  .catch(err => {
    console.error('❌ Test failed:', err);
  });
