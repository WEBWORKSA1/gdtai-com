/* GDTai runtime configuration — edit freely, no rebuild needed. */
window.GDT_CONFIG = {
  adClient: "ca-pub-6620975821265271",
  /* Optional manual AdSense ad-unit slot IDs. Leave empty to rely on Auto ads
     (enable Auto ads for this site in your AdSense dashboard). */
  adSlots: { inline: "", side: "" },
  /* Optional donation links. When empty, donation buttons open the pledge form
     and you reply with a payment link. Examples:
     paypal: "https://www.paypal.com/donate/?hosted_button_id=XXXX"
     kofi: "https://ko-fi.com/yourname", buymeacoffee: "https://buymeacoffee.com/yourname"
     upi: "upi://pay?pa=yourid@bank&pn=GDTai", github: "https://github.com/sponsors/yourname" */
  donate: { paypal: "", kofi: "", buymeacoffee: "", upi: "", github: "" }
};
(function () {
  try {
    if (localStorage.getItem("gdt-consent") === "essential") {
      (window.adsbygoogle = window.adsbygoogle || []).requestNonPersonalizedAds = 1;
    }
  } catch (e) {}
})();
