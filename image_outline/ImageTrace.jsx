/*  Batch Image Trace (Preset) -> Expand -> Export SVG
    - Selects "Layer 1" (or first layer if not found)
    - Traces first raster/placed item found on that layer
    - Applies preset: Polina_Test_Contour
    - Expands tracing
    - Exports SVG to output folder
*/

// #target illustrator

(function () {
    if (app.documents.length > 0) {
        // Avoid any weird "global" selection state
        app.activeDocument.selection = null;
    }

    var PRESET_NAME = "Polina_Test_Contour"; // must match your Image Trace preset name exactly

    // Pick folders
    var inFolder = Folder.selectDialog("Select the INPUT folder with images (PNG/JPG/TIF)...");
    if (!inFolder) return;

    var outFolder = Folder.selectDialog("Select the OUTPUT folder for SVGs...");
    if (!outFolder) return;

    // Create a tiny proof file in output folder to verify write access
    var proof = new File(outFolder.fsName + "/__can_write__.txt");
    if (!proof.open("w")) {
        alert("Cannot write to output folder:\n" + outFolder.fsName);
        return;
    }
    proof.writeln("ok");
    proof.close();

    // Log file for debugging
    var logFile = new File(outFolder.fsName + "/__trace_log__.txt");
    if (!logFile.open("w")) {
        alert("Cannot create log file in output folder:\n" + outFolder.fsName);
        return;
    }
    logFile.writeln("Starting batch...");

    // Collect files
    var files = inFolder.getFiles(function (f) {
        if (!(f instanceof File)) return false;
        return /\.(png|jpg|jpeg|tif|tiff)$/i.test(f.name);
    });

    if (!files || files.length === 0) {
        alert("No PNG/JPG/TIF files found in the selected folder.");
        return;
    }

    // SVG export options
    var svgOpts = new ExportOptionsSVG();
    // Keep SVG simple + Rhino-friendly
    svgOpts.embedRasterImages = false;
    svgOpts.fontSubsetting = SVGFontSubsetting.None;
    svgOpts.coordinatePrecision = 3;
    svgOpts.cssProperties = SVGCSSPropertyLocation.PRESENTATIONATTRIBUTES;
    svgOpts.documentEncoding = SVGDocumentEncoding.UTF8;

    function getLayer1(doc) {
        // Try by name first, then fallback to first layer
        try {
            var lyr = doc.layers.getByName("Layer 1");
            return lyr;
        } catch (e) {
            return doc.layers[0];
        }
    }

    function findFirstImageOnLayer(layer) {
        // Search for PlacedItem or RasterItem within layer.pageItems
        // (PlacedItem is common when you open/place PNGs)
        for (var i = 0; i < layer.pageItems.length; i++) {
            var it = layer.pageItems[i];
            if (it.locked || it.hidden) continue;

            if (it.typename === "PlacedItem") return it;
            if (it.typename === "RasterItem") return it;
        }
        return null;
    }

    function applyTracePresetAndExpand(doc, item) {
        doc.selection = null;

        // If it's placed, embed it so trace works consistently
        if (item.typename === "PlacedItem") {
            try {
                item.embed();
            } catch (e1) {
                // If embed fails, still try tracing; some builds handle it
            }
        }

        // After embed, the original reference may not be valid; refind first raster
        // (Embedding can replace the object)
        var layer = getLayer1(doc);
        var img = findFirstImageOnLayer(layer);

        if (!img) throw new Error("No PlacedItem/RasterItem found on Layer 1.");

        // Select it
        img.selected = true;

        // Trace using DOM if available
        // RasterItem.trace() returns a TracingObject in many Illustrator versions
        var tracingObj = null;

        try {
            if (img.trace) {
                tracingObj = img.trace();
            } else {
                // Fallback: menu command to create tracing object (less ideal)
                app.executeMenuCommand("Live Trace"); // may not exist in all versions
            }
        } catch (e2) {
            // If trace() fails, try menu command fallback
            try {
                app.executeMenuCommand("Live Trace");
            } catch (e3) {
                throw new Error("Could not start Image Trace. Try embedding the image first or verify Illustrator supports tracing via scripting.");
            }
        }

        // Apply preset
        // If we got a tracing object, set preset via tracingOptions
        if (tracingObj && tracingObj.tracingOptions) {
            try {
                tracingObj.tracingOptions.loadFromPreset(PRESET_NAME);
            } catch (e4) {
                throw new Error(
                    "Could not load preset '" + PRESET_NAME + "'.\n" +
                    "Make sure it exists in Image Trace Presets and the name matches exactly."
                );
            }

            // Expand to paths
            try {
                tracingObj.expandTracing();
            } catch (e5) {
                // Fallback expand via menu command
                app.executeMenuCommand("expandStyle");
            }
        } else {
            // If we couldn't get the tracing object, attempt preset + expand via menu
            // (This is less reliable across versions)
            throw new Error("Tracing object not accessible via scripting in this Illustrator build. Try the DOM trace() route by ensuring the item is embedded/raster.");
        }

        doc.selection = null;
    }

    function exportAsSVG(doc, outFolder, originalFileName) {
        var base = originalFileName.replace(/\.[^\.]+$/, "");
        var outFile = new File(outFolder.fsName + "/" + base + "_contour.svg");
        doc.exportFile(outFile, ExportType.SVG, svgOpts);
    }

    var failures = [];
    for (var f = 0; f < files.length; f++) {
        var file = files[f];
        try {
            var doc = app.open(file);

            // Make sure we’re not in Outline mode etc; not strictly required
            doc.selection = null;

            var layer1 = getLayer1(doc);
            var imgItem = findFirstImageOnLayer(layer1);
            if (!imgItem) throw new Error("No image found on Layer 1.");

            applyTracePresetAndExpand(doc, imgItem);
            exportAsSVG(doc, outFolder, file.name);

            // Close without saving AI
            doc.close(SaveOptions.DONOTSAVECHANGES);
        } catch (err) {
            try { if (app.documents.length) app.activeDocument.close(SaveOptions.DONOTSAVECHANGES); } catch (eClose) {}
            failures.push(file.name + " → " + err.message);
        }
    }

    if (failures.length) {
        alert("Done with errors:\n\n" + failures.join("\n"));
    } else {
        alert("Done! Exported " + files.length + " SVG files.");
    }
})();