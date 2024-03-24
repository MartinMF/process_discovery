// based on: https://stackoverflow.com/questions/38477972/javascript-save-svg-element-to-file-on-disk

let get_svg_export_button = function(svg) {
  let clone = svg.cloneNode(true);
  parseStyles(clone);
  let svgDocType = document.implementation.createDocumentType('svg', "-//W3C//DTD SVG 1.1//EN", "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd");
  let svgDoc = document.implementation.createDocument('http://www.w3.org/2000/svg', 'svg', svgDocType);
  svgDoc.replaceChild(clone, svgDoc.documentElement);
  let svgData = (new XMLSerializer()).serializeToString(svgDoc);

  let button = document.createElement('button');
  button.addEventListener('click', () => {
      let blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
      let url = URL.createObjectURL(blob);
      let link = document.createElement('a');
      link.href = url;
      link.download = 'graph.svg';
      link.click();
      URL.revokeObjectURL(url);
  });
  // button.textContent = 'Download SVG';
  button.innerHTML ='SVG <i class="fa fa-download"></i>'
  // button.style.border = "1px solid red";
  // button.style.borderRadius = "100vw";
  button.style.margin = "5px";
  return button;
};

let parseStyles = function(svg) {
  let styleSheets = [];
  let i;
  let docStyles = svg.ownerDocument.styleSheets;
  for (i = 0; i < docStyles.length; i++) {
    styleSheets.push(docStyles[i]);
  }

  if (!styleSheets.length) {
    return;
  }

  let defs = svg.querySelector('defs') || document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  if (!defs.parentNode) {
    svg.insertBefore(defs, svg.firstElementChild);
  }
  svg.matches = svg.matches || svg.webkitMatchesSelector || svg.mozMatchesSelector || svg.msMatchesSelector || svg.oMatchesSelector;

  for (i = 0; i < styleSheets.length; i++) {
    let currentStyle = styleSheets[i]

    let rules;
    try {
      rules = currentStyle.cssRules;
    } catch (e) {
      continue;
    }
    let style = document.createElement('style');
    let l = rules && rules.length;
    for (let j = 0; j < l; j++) {
      let selector = rules[j].selectorText;
      if (!selector) {
        continue;
      }
      if ((svg.matches && svg.matches(selector)) || svg.querySelector(selector)) {

        let cssText = rules[j].cssText;
        style.innerHTML += cssText + '\n';
      }
    }
    if (style.innerHTML) {
      defs.appendChild(style);
    }
  }

};