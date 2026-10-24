// PostHog product analytics for focusland.co: pageviews, clicks (autocapture) and a few named events.
// Every page loads this file with <script src="/analytics.js"></script> in its <head>.
// New pages and articles must keep that line.
(function () {
  var KEY = 'phc_rjtBJpxEyUKVanuLPRigDWDBgzgcyVK8vMW343yvEjmX';
  var HOST = 'https://us.i.posthog.com';

  // PostHog's official loader snippet.
  !function(t,e){var o,n,p,r;e.__SV||(window.posthog&&window.posthog.__loaded)||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);

  posthog.init(KEY, {
    api_host: HOST,
    person_profiles: 'identified_only',
    capture_pageview: true,
    capture_pageleave: true,
    autocapture: true,
    disable_session_recording: true
  });

  // Named events, so the important clicks are easy to find in PostHog.
  function named(a) {
    var href = a.getAttribute('href') || '';
    var text = (a.textContent || '').trim();
    if (/coming soon on iphone/i.test(text)) return ['clicked coming soon', {}];
    if (/^say hi$/i.test(text)) return ['clicked say hi', {}];
    if (href.indexOf('instagram.com') !== -1) return ['clicked instagram', {}];
    if (href.indexOf('mailto:') === 0) return ['clicked email support', {}];
    if (href.indexOf('mail.google.com') !== -1) return ['clicked open in gmail', {}];
    if (a.classList.contains('post')) {
      var title = a.querySelector('h2, h3');
      return ['clicked article card', { article: href, title: title ? title.textContent.trim() : text }];
    }
    return null;
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a');
    if (!a) return;
    var event = named(a);
    if (event) posthog.capture(event[0], event[1]);
  }, true);
})();
