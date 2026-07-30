(function () {
  var W = 1600,
    H = 900;
  var COLORS = {
    bg: "#131210",
    accent: "#8fa0ff",
    muted: "#33322b",
    text: "#ece9e0",
  };

  document.addEventListener("DOMContentLoaded", function () {
    var app = document.getElementById("cover-generator-app");
    if (!app) {
      return;
    }

    var canvas = document.getElementById("cover-generator-canvas");
    var ctx = canvas.getContext("2d");
    var titleInput = document.getElementById("cover-generator-title");
    var eyebrowInput = document.getElementById("cover-generator-eyebrow");
    var regenerateBtn = document.getElementById("cover-generator-regenerate");
    var downloadBtn = document.getElementById("cover-generator-download");

    var blobLayout = null;
    var grainPattern = null;
    var fontReady = false;

    function rand(min, max) {
      return min + Math.random() * (max - min);
    }

    function generateBlobLayout() {
      return {
        blobs: [
          { x: rand(0.55, 0.95) * W, y: rand(0.05, 0.35) * H, r: rand(280, 420), color: COLORS.accent, alpha: 0.55 },
          { x: rand(0.65, 1.05) * W, y: rand(0.35, 0.7) * H, r: rand(220, 360), color: COLORS.accent, alpha: 0.3 },
          { x: rand(0.0, 0.35) * W, y: rand(0.6, 1.0) * H, r: rand(200, 320), color: COLORS.muted, alpha: 0.7 },
        ],
      };
    }

    function hexToRgb(hex) {
      var v = parseInt(hex.replace("#", ""), 16);
      return { r: (v >> 16) & 255, g: (v >> 8) & 255, b: v & 255 };
    }

    function rgba(hex, alpha) {
      var c = hexToRgb(hex);
      return "rgba(" + c.r + "," + c.g + "," + c.b + "," + alpha + ")";
    }

    function buildGrainPattern() {
      var size = 128;
      var c = document.createElement("canvas");
      c.width = size;
      c.height = size;
      var gctx = c.getContext("2d");
      var imgData = gctx.createImageData(size, size);
      for (var i = 0; i < imgData.data.length; i += 4) {
        var v = Math.floor(Math.random() * 255);
        imgData.data[i] = v;
        imgData.data[i + 1] = v;
        imgData.data[i + 2] = v;
        imgData.data[i + 3] = 255;
      }
      gctx.putImageData(imgData, 0, 0);
      return ctx.createPattern(c, "repeat");
    }

    function drawGrain() {
      if (!grainPattern) {
        grainPattern = buildGrainPattern();
      }
      ctx.save();
      ctx.globalAlpha = 0.05;
      ctx.globalCompositeOperation = "overlay";
      ctx.fillStyle = grainPattern;
      ctx.fillRect(0, 0, W, H);
      ctx.restore();
    }

    function drawBlobs() {
      blobLayout.blobs.forEach(function (b) {
        var g = ctx.createRadialGradient(b.x, b.y, 0, b.x, b.y, b.r);
        g.addColorStop(0, rgba(b.color, b.alpha));
        g.addColorStop(1, rgba(b.color, 0));
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, W, H);
      });
    }

    function wrapText(text, maxWidth, font) {
      ctx.font = font;
      var words = text.split(" ");
      var lines = [];
      var current = "";
      for (var i = 0; i < words.length; i++) {
        var word = words[i];
        var test = current ? current + " " + word : word;
        if (ctx.measureText(test).width > maxWidth && current) {
          lines.push(current);
          current = word;
        } else {
          current = test;
        }
      }
      if (current) {
        lines.push(current);
      }
      return lines;
    }

    function drawLetterSpaced(text, x, y, spacing) {
      var cx = x;
      for (var i = 0; i < text.length; i++) {
        var ch = text[i];
        ctx.fillText(ch, cx, y);
        cx += ctx.measureText(ch).width + spacing;
      }
    }

    function drawText() {
      var marginX = 90;
      var marginBottom = 90;
      var maxWidth = W - marginX * 2 - 120;

      var eyebrow = eyebrowInput.value.trim().toUpperCase();
      var title = titleInput.value.trim() || "Untitled post";

      var titleSize = 108;
      var minSize = 52;
      var titleLines = [];
      while (titleSize >= minSize) {
        titleLines = wrapText(title, maxWidth, '700 ' + titleSize + 'px "Clash Display"');
        if (titleLines.length <= 3) {
          break;
        }
        titleSize -= 4;
      }
      var titleLineHeight = titleSize * 1.05;

      var eyebrowSize = 26;
      var eyebrowGap = eyebrow ? 30 : 0;
      var eyebrowHeight = eyebrow ? eyebrowSize : 0;

      var blockHeight = eyebrowHeight + eyebrowGap + titleLines.length * titleLineHeight;
      var y = H - marginBottom - blockHeight;

      ctx.textBaseline = "top";

      if (eyebrow) {
        ctx.font = '700 ' + eyebrowSize + 'px "Clash Display"';
        ctx.fillStyle = COLORS.accent;
        drawLetterSpaced(eyebrow, marginX, y, eyebrowSize * 0.08);
        y += eyebrowHeight + eyebrowGap;
      }

      ctx.font = '700 ' + titleSize + 'px "Clash Display"';
      ctx.fillStyle = COLORS.text;
      for (var i = 0; i < titleLines.length; i++) {
        ctx.fillText(titleLines[i], marginX, y);
        y += titleLineHeight;
      }
    }

    function draw() {
      if (!fontReady || !blobLayout) {
        return;
      }
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = COLORS.bg;
      ctx.fillRect(0, 0, W, H);
      drawBlobs();
      drawGrain();
      drawText();
    }

    regenerateBtn.addEventListener("click", function () {
      blobLayout = generateBlobLayout();
      grainPattern = null;
      draw();
    });

    downloadBtn.addEventListener("click", function () {
      canvas.toBlob(
        function (blob) {
          var url = URL.createObjectURL(blob);
          var a = document.createElement("a");
          var slug =
            (titleInput.value || "cover")
              .toLowerCase()
              .trim()
              .replace(/[^a-z0-9]+/g, "-")
              .replace(/(^-|-$)/g, "") || "cover";
          a.href = url;
          a.download = slug + ".webp";
          a.click();
          URL.revokeObjectURL(url);
        },
        "image/webp",
        0.92
      );
    });

    titleInput.addEventListener("input", draw);
    eyebrowInput.addEventListener("input", draw);

    blobLayout = generateBlobLayout();

    var fontUrl = app.dataset.fontUrl;
    var clashFont = new FontFace("Clash Display", 'url("' + fontUrl + '")', {
      weight: "700",
    });
    clashFont.load().then(function (loaded) {
      document.fonts.add(loaded);
      fontReady = true;
      draw();
    });
  });
})();
