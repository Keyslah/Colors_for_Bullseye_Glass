/**
 * Purpose: filter Add Colors by Bullseye's published color families.
 * Setup: imported by cart-library.js; matches existing catalog style IDs.
 * Destructive behavior: none; these groups only narrow the visible add results.
 * Constraints: no color-matching or purchase metadata is changed.
 * Sources: https://www.bullseyeglass.com/about-our-glass/ and each family's
 * About Our Glass page, checked 2026-11-20. Overlapping groups are intentional.
 * Blue Black is also in https://shop.bullseyeglass.com/collections/black.
 * Medieval Green, Light Mineral Green and Dark Amber Tint are absent from the
 * family pages; group these by their explicit catalog color names.
 */
export const CART_COLOR_FAMILIES = Object.freeze([
  Object.freeze({id:'all',label:'All',color:'#ffffff',styles:Object.freeze([])}),
  Object.freeze({id:"red",label:"Red",color:"#c83439",styles:Object.freeze(["000024","000034","000124","000224","000225","000421","001122","001215","001311","001322","001332","001821","001823","001824","001831","001932"])}),
  Object.freeze({id:"orange",label:"Orange",color:"#ee8438",styles:Object.freeze(["000025","000034","000125","000305","000309","000321","000329","000435","001025","001125","001205","001305","001321","001823","001834","001857","001934"])}),
  Object.freeze({id:"yellow",label:"Yellow",color:"#e5ce46",styles:Object.freeze(["000120","000137","000220","000221","000227","000320","000337","000420","001120","001126","001137","001138","001320","001437","001701","001820","001826","001827","001837","001838","001920"])}),
  Object.freeze({id:"green",label:"Green",color:"#4b8656",styles:Object.freeze(["000112","000117","000126","000131","000141","000144","000145","000207","000212","000221","000222","000227","000241","000312","000345","001107","001112","001126","001141","001145","001207","001217","001226","001241","001242","001247","001412","001417","001422","001426","001439","001707","001717","001807","001826","001841","001844","001845","001858","001859","001867","001877","001917","001977"])}),
  Object.freeze({id:"blue-green",label:"Blue-Green",color:"#37949c",styles:Object.freeze(["000116","000144","000146","000148","000161","000164","000216","001108","001116","001118","001140","001176","001246","001406","001408","001416","001444","001717","001806","001808","001816"])}),
  Object.freeze({id:"blue",label:"Blue",color:"#3d71af",styles:Object.freeze(["000104","000108","000114","000116","000118","000146","000147","000148","000161","000164","000208","000216","001108","001114","001116","001118","001140","001164","001176","001246","001406","001408","001414","001416","001444","001464","001714","001806","001808","001814","001816","001818","001864","001948"])}),
  Object.freeze({id:"purple",label:"Purple & Violet",color:"#8956a4",styles:Object.freeze(["000118","000142","000303","000304","000332","000334","000434","001105","001128","001228","001234","001334","001405","001428","001442","001842","001844","001948","001964"])}),
  Object.freeze({id:"black",label:"Black",color:"#242424",styles:Object.freeze(["000100","000101","000102"])}),
  Object.freeze({id:"gray",label:"Gray",color:"#969797",styles:Object.freeze(["000119","000132","000136","000206","000236","000336","000349","001129","001229","001429","001449","001829","001864","001964"])}),
  Object.freeze({id:"white",label:"White & Clear",color:"#faf9f2",styles:Object.freeze(["000009","000013","000113","000127","000137","000138","000139","000143","000243","000313","000403","000420","000843","000920","001009","001015","001016","001019","001100","001101","001401"])}),
  Object.freeze({id:"neutral-brown",label:"Neutrals",color:"#b08b65",styles:Object.freeze(["000034","000119","000127","000137","000138","000139","000203","000309","000310","000329","000337","000420","001109","001119","001149","001409","001419","001439","001819","001858","001859"])}),
  Object.freeze({id:"pink",label:"Pink",color:"#d886ac",styles:Object.freeze(["000034","000301","000305","000421","000431","000435","001215","001311","001332","001821","001824","001831","001932"])}),
]);

export function inCartColorFamily(product, family = 'all') {
  if (family === 'all') return true;
  const group = CART_COLOR_FAMILIES.find(option => option.id === family);
  return Boolean(group && (family === 'white' && product?.isClear || group.styles.includes(String(product?.id || ''))));
}

