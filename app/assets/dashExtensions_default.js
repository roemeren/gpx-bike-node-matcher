window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        // --- custom icon with full HTML/CSS customization (not possible in Python) ---
        nodePointToLayer: function(feature, latlng) {
            const label = feature.properties.rcn_ref || "";
            const icon = L.divIcon({
                className: "custom-label-icon",
                html: `<div style="
                    background-color: #FEFDEF;
                    color: black;
                    width: 40px;
                    height: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                    font-weight: bold;
                    font-size: 16px;
                    font-family: 'Segoe UI', sans-serif;
                    border: 4px solid #33A7AA;
                ">${label}</div>`,
                iconSize: [40, 40],
                iconAnchor: [20, 20]
            });

            return L.marker(latlng, {
                icon: icon
            });
        },

        // --- style function for segments ---
        segmentStyle: function(feature, context) {
            const { weight_classes, weights, color } = context.hideout;
            const value = feature.properties.count_track || 0;

            let w = weights[0]; // default weight
            for (let i = 0; i < weight_classes.length; i++) {
                if (value > weight_classes[i]) {
                    w = weights[i + 1];
                }
            }

            return {color: color, weight: w};
        },

        // --- selected style (persistent highlight) ---
        trackStyle: function(feature, context) {
            const hideout = context && context.hideout ? context.hideout : {};
            const baseColor = hideout.base_color;
            // const selectedColor = hideout.selected_color;
            const trackFocus = hideout.track_focus;
            
            // set base style for all features
            const baseStyle = { color: baseColor, weight: 1, opacity: 0.6 };
            
            // override style for selected feature
            if (trackFocus) {
                const selectedId = hideout.selected_id;
                const selectedKey = hideout.selected_key;
        
                const featId = feature.properties && feature.properties[selectedKey];
                if (selectedId && featId === selectedId) {
                    // use separate color for selected track
                    // return { ...baseStyle, color: selectedColor, weight: 8, opacity: 0.5};
                    // use same color
                    return { ...baseStyle, weight: 8, opacity: 0.5};
                }
            }

            return baseStyle;
        },

        // --- hover style overrides current style ---
        trackHoverStyle: function(feature, _) {
            // override the feature's current styling with a custom weight
            return { ...feature.options, weight: 8 };
        },

        // attach tooltips to each GeoJSON feature using precomputed HTML ---
        trackBindTooltip: function(feature, layer, context) {
            // get unique track id from feature properties
            const fid = feature.properties.track_uid;
            if (fid && context.hideout.tooltips[fid]) {
                layer.bindTooltip(context.hideout.tooltips[fid], {
                    direction: "top",
                    opacity: context.hideout.tooltip_opacity
                });
            }
        },

    }
});