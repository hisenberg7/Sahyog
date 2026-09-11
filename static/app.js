document.addEventListener("DOMContentLoaded", () => {

  "use strict";


  /* =========================================================
     THEME TOGGLE
     ========================================================= */

  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");
  const themeLabel = document.getElementById("themeLabel");


  const applyThemeUI = (t) => {

    if (!themeIcon || !themeLabel) return;

    if (t === "dark") {

      themeIcon.className = "bi bi-moon-stars-fill";
      themeLabel.textContent = "Dark";

    } else {

      themeIcon.className = "bi bi-sun-fill";
      themeLabel.textContent = "Light";

    }

  };


  let savedTheme = "light";

  try {
    savedTheme =
      localStorage.getItem("sahyog-theme") === "dark"
        ? "dark"
        : "light";
  } catch (e) {
    savedTheme = "light";
  }


  applyThemeUI(savedTheme);


  themeToggle?.addEventListener("click", () => {

    const current =
      document.documentElement.getAttribute("data-theme") === "dark"
        ? "dark"
        : "light";

    const next =
      current === "dark"
        ? "light"
        : "dark";


    document.documentElement.setAttribute(
      "data-theme",
      next
    );


    try {
      localStorage.setItem(
        "sahyog-theme",
        next
      );
    } catch (e) {}


    applyThemeUI(next);

  });



  /* =========================================================
     MULTILINGUAL UI
     
     Django already translates strings using {% trans %}.
     This layer additionally translates hard-coded UI text
     which was not wrapped in Django translation tags.
     ========================================================= */


  /*
   * Detect the active language from the page, Django's language cookie,
   * or the browser/local preference.  This is important because Django's
   * hard-coded template text may still render while <html lang="en"> is
   * present.
   */
  function getCookie(name) {
    const prefix = `${name}=`;
    const cookie = document.cookie
      .split(";")
      .map(item => item.trim())
      .find(item => item.startsWith(prefix));

    return cookie
      ? decodeURIComponent(cookie.substring(prefix.length))
      : "";
  }

  function normalizeLanguage(value) {
    const lang = String(value || "")
      .toLowerCase()
      .trim()
      .replace("_", "-");

    if (lang.startsWith("hi")) return "hi";
    if (lang.startsWith("bn")) return "bn";
    return "en";
  }

  const languageCandidates = [
    document.documentElement.getAttribute("lang"),
    document.documentElement.dataset.language,
    document.documentElement.dataset.lang,
    getCookie("django_language"),
    getCookie("language"),
    (() => {
      try {
        return localStorage.getItem("sahyog-language");
      } catch (e) {
        return "";
      }
    })(),
    (() => {
      try {
        return localStorage.getItem("language");
      } catch (e) {
        return "";
      }
    })()
  ];

  const language =
    languageCandidates
      .map(normalizeLanguage)
      .find(lang => lang === "hi" || lang === "bn") || "en";


  if (language !== "hi" && language !== "bn") {
    // English needs no client-side translation.
  } else {


    const translations = {

      hi: {

        /* Navigation */
        "Home": "होम",
        "Find Workers": "कामगार खोजें",
        "Find workers": "कामगार खोजें",
        "Dashboard": "डैशबोर्ड",
        "Cooperative": "सहकारी समिति",
        "Logout": "लॉगआउट",
        "Login": "लॉगिन",
        "Get Started": "शुरू करें",
        "Profile": "प्रोफ़ाइल",
        "My Profile": "मेरी प्रोफ़ाइल",
        "My Services": "मेरी सेवाएं",
        "My Dashboard": "मेरा डैशबोर्ड",
        "My Bookings": "मेरी बुकिंग",
        "Worker Dashboard": "कामगार डैशबोर्ड",
        "Welfare": "कल्याण",
        "Welfare & Protection": "कल्याण एवं सुरक्षा",
        "Cooperative Control Center": "सहकारी नियंत्रण केंद्र",
        "Django Admin": "डिजैंगो व्यवस्थापक",

        /* Customer dashboard */
        "Customer workspace": "ग्राहक कार्यक्षेत्र",
        "What's the work you need help with,": "आपको किस काम में मदद चाहिए,",
        "Book trusted local help and keep every job in one place.": "भरोसेमंद स्थानीय मदद बुक करें और अपने सभी काम एक ही जगह पर रखें।",
        "Find a worker": "कामगार खोजें",
        "All bookings": "सभी बुकिंग",
        "Total bookings": "कुल बुकिंग",
        "Awaiting worker": "कामगार की प्रतीक्षा",
        "Active jobs": "सक्रिय काम",
        "Completed": "पूरा हुआ",
        "Recent bookings": "हाल की बुकिंग",
        "Track your service requests.": "अपनी सेवा बुकिंग को ट्रैक करें।",
        "Emergency": "आपातकालीन",
        "Rate": "रेटिंग दें",
        "Pay": "भुगतान करें",
        "Invoice": "चालान",
        "No bookings yet.": "अभी कोई बुकिंग नहीं है।",
        "Find a trusted worker and make your first booking.": "भरोसेमंद कामगार खोजें और अपनी पहली बुकिंग करें।",
        "Browse services": "सेवाएं देखें",
        "Need help fast?": "जल्दी मदद चाहिए?",
        "Emergency requests are prioritized.": "आपातकालीन अनुरोधों को प्राथमिकता दी जाती है।",
        "Choose a service, allow location and use the emergency workflow to send a priority request.": "सेवा चुनें, लोकेशन की अनुमति दें और प्राथमिकता अनुरोध भेजने के लिए आपातकालीन प्रक्रिया का उपयोग करें।",
        "Find emergency-ready worker": "आपातकालीन सेवा वाला कामगार खोजें",
        "Only verified providers can receive new bookings.": "केवल सत्यापित सेवा प्रदाता नई बुकिंग प्राप्त कर सकते हैं।",

        /* Worker dashboard */
        "Worker workspace": "कामगार कार्यक्षेत्र",
        "Build your local reputation.": "अपनी स्थानीय प्रतिष्ठा बनाएं।",
        "Manage requests, services, earnings and your verification status.": "अनुरोध, सेवाएं, कमाई और सत्यापन स्थिति प्रबंधित करें।",
        "Add service": "सेवा जोड़ें",
        "Active bookings": "सक्रिय बुकिंग",
        "Completed jobs": "पूरे किए गए काम",
        "Worker rating": "कामगार रेटिंग",
        "Completed value": "पूरे किए गए काम का मूल्य",
        "Booking requests": "बुकिंग अनुरोध",
        "Accept only when you can deliver the job.": "केवल तभी स्वीकार करें जब आप काम पूरा कर सकें।",
        "Accept": "स्वीकार करें",
        "Reject": "अस्वीकार करें",
        "No new requests.": "कोई नया अनुरोध नहीं है।",
        "New customer requests will appear here.": "नए ग्राहक अनुरोध यहां दिखाई देंगे।",
        "Quick actions": "त्वरित कार्य",
        "Keep your profile job-ready.": "अपनी प्रोफ़ाइल को काम के लिए तैयार रखें।",
        "Your jobs": "आपके काम",
        "Use the workflow to move accepted jobs forward.": "स्वीकृत कामों को आगे बढ़ाने के लिए इस प्रक्रिया का उपयोग करें।",
        "On the Way": "रास्ते में",
        "Arrived": "पहुंच गए",
        "Start": "शुरू करें",
        "Complete": "पूरा करें",
        "No jobs yet.": "अभी कोई काम नहीं है।",
        "Completed value": "पूर्ण कार्य मूल्य",

        /* Verification */
        "Verified worker": "सत्यापित कामगार",
        "Verification": "सत्यापन",
        "under review": "समीक्षा में",
        "needed": "आवश्यक",
        "Your profile can receive trusted bookings.": "आपकी प्रोफ़ाइल भरोसेमंद बुकिंग प्राप्त कर सकती है।",
        "Submit a document/certification from your profile so the cooperative can review you.": "सहकारी समिति द्वारा समीक्षा के लिए अपनी प्रोफ़ाइल से दस्तावेज़ या प्रमाणपत्र जमा करें।",
        "View profile": "प्रोफ़ाइल देखें",
        "Complete verification": "सत्यापन पूरा करें",

        /* Marketplace */
        "Marketplace": "सेवा बाज़ार",
        "Find trusted local help.": "भरोसेमंद स्थानीय मदद खोजें।",
        "Verified providers, clear pricing and smart matching.": "सत्यापित प्रदाता, स्पष्ट कीमत और स्मार्ट मिलान।",
        "Use my location": "मेरी लोकेशन का उपयोग करें",
        "All categories": "सभी श्रेणियां",
        "Search": "खोजें",
        "Smart matching enabled — results are ranked by proximity and worker trust signals.": "स्मार्ट मिलान सक्रिय है — परिणाम दूरी और कामगार के भरोसे के आधार पर क्रमबद्ध हैं।",
        "services available": "सेवाएं उपलब्ध",
        "Verified providers are prioritized": "सत्यापित प्रदाताओं को प्राथमिकता दी जाती है",
        "Verified": "सत्यापित",
        "Verification pending": "सत्यापन लंबित",
        "Starting from": "शुरुआती कीमत",
        "Book": "बुक करें",
        "Not bookable": "बुकिंग उपलब्ध नहीं",
        "No matching services": "कोई मिलती-जुलती सेवा नहीं मिली",
        "Try another category or search term.": "कोई दूसरी श्रेणी या खोज शब्द आज़माएं।",

        /* Booking */
        "Back to services": "सेवाओं पर वापस जाएं",
        "Booking request": "बुकिंग अनुरोध",
        "Emergency request": "आपातकालीन अनुरोध",
        "We’ll prioritize this booking with the verified worker network.": "सत्यापित कामगार नेटवर्क इस बुकिंग को प्राथमिकता देगा।",
        "Service address": "सेवा का पता",
        "Date": "तारीख",
        "Preferred time": "पसंदीदा समय",
        "Use my current location": "मेरी वर्तमान लोकेशन का उपयोग करें",
        "Your location is used only to improve worker matching.": "आपकी लोकेशन का उपयोग केवल कामगार मिलान बेहतर करने के लिए किया जाता है।",
        "Confirm Booking Request": "बुकिंग अनुरोध की पुष्टि करें",
        "Send Emergency Request": "आपातकालीन अनुरोध भेजें",

        /* Payment */
        "Choose Payment Method": "भुगतान का तरीका चुनें",
        "Online / UPI": "ऑनलाइन / UPI",
        "Cash": "नकद",
        "Payment": "भुगतान",

        /* Invoice */
        "Service invoice": "सेवा चालान",
        "Customer": "ग्राहक",
        "Provider": "सेवा प्रदाता",
        "Service subtotal": "सेवा उप-योग",
        "Cooperative platform fee (5%)": "सहकारी प्लेटफ़ॉर्म शुल्क (5%)",
        "Total": "कुल",
        "Worker earnings after platform fee:": "प्लेटफ़ॉर्म शुल्क के बाद कामगार की कमाई:",
        "Payment status:": "भुगतान स्थिति:",
        "Print / Save": "प्रिंट / सेव करें",

        /* Dynamic billing */
        "Dynamic Billing": "डायनामिक बिलिंग",
        "Base": "मूल राशि",
        "Base service": "मूल सेवा शुल्क",
        "Emergency fee": "आपातकालीन शुल्क",
        "Approved extras": "स्वीकृत अतिरिक्त शुल्क",
        "Final amount": "अंतिम राशि",
        "Final payable": "अंतिम देय राशि",
        "Extra charges": "अतिरिक्त शुल्क",
        "Parts / Material": "पार्ट्स / सामग्री",
        "Additional Labour": "अतिरिक्त श्रम",
        "Additional Service": "अतिरिक्त सेवा",
        "Other": "अन्य",
        "Description": "विवरण",
        "Quantity": "मात्रा",
        "Unit price": "प्रति इकाई कीमत",
        "Unit Price": "प्रति इकाई कीमत",
        "Total": "कुल",
        "Awaiting Customer Approval": "ग्राहक की मंजूरी की प्रतीक्षा",
        "Approved": "स्वीकृत",
        "Rejected": "अस्वीकृत",
        "Add charge": "शुल्क जोड़ें",
        "Add Extra Charge": "अतिरिक्त शुल्क जोड़ें",
        "Customer approval required": "ग्राहक की मंजूरी आवश्यक है",
        "Approve": "मंजूर करें",
        "Reject": "अस्वीकार करें",
        "Customer note": "ग्राहक का नोट",
        "Optional note": "वैकल्पिक नोट",

        /* Rating */
        "Thank you! Your rating and feedback have been submitted.": "धन्यवाद! आपकी रेटिंग और प्रतिक्रिया जमा कर दी गई है।",

        /* Welfare */
        "Worker protection": "कामगार सुरक्षा",
        "Welfare & insurance": "कल्याण एवं बीमा",
        "Build a stronger safety net through the cooperative.": "सहकारी समिति के माध्यम से एक मजबूत सुरक्षा व्यवस्था बनाएं।",
        "Current plan": "वर्तमान योजना",
        "Coverage": "कवरेज",
        "Monthly contribution": "मासिक योगदान",
        "Protection plan": "सुरक्षा योजना",
        "Enroll me in the cooperative welfare plan": "मुझे सहकारी कल्याण योजना में शामिल करें",
        "Keep emergency support enabled": "आपातकालीन सहायता सक्रिय रखें",
        "Notes": "नोट्स",
        "Save welfare preferences": "कल्याण प्राथमिकताएं सेव करें",
        "Protected": "सुरक्षित",
        "Setup needed": "सेटअप आवश्यक",

        /* Admin */
        "Cooperative control center": "सहकारी नियंत्रण केंद्र",
        "Run the network.": "नेटवर्क संचालित करें।",
        "Trust, operations, payments, worker welfare and demand intelligence in one place.": "भरोसा, संचालन, भुगतान, कामगार कल्याण और मांग की जानकारी एक ही जगह।",
        "Admin": "व्यवस्थापक",
        "View platform": "प्लेटफ़ॉर्म देखें",
        "Workers": "कामगार",
        "Bookings": "बुकिंग",
        "Network volume": "नेटवर्क गतिविधि",
        "Verified revenue": "सत्यापित राजस्व",
        "Payment ledger": "भुगतान लेजर",
        "Needs attention": "ध्यान देने की आवश्यकता",
        "Verification queue": "सत्यापन कतार",
        "Review workers waiting for cooperative approval.": "सहकारी समिति की मंजूरी की प्रतीक्षा कर रहे कामगारों की समीक्षा करें।",
        "Review": "समीक्षा करें",
        "Verification queue is clear.": "सत्यापन कतार खाली है।",
        "Network pulse": "नेटवर्क गतिविधि",
        "Last 30 days of booking activity.": "पिछले 30 दिनों की बुकिंग गतिविधि।",
        "Payment review": "भुगतान समीक्षा",
        "Verify customer UPI submissions before marking the ledger paid.": "लेजर को भुगतान किया हुआ चिह्नित करने से पहले ग्राहक के UPI भुगतान की पुष्टि करें।",
        "Verify": "सत्यापित करें",
        "No payment submissions yet.": "अभी कोई भुगतान जमा नहीं हुआ है।",
        "Worker protection": "कामगार सुरक्षा",
        "Cooperative welfare coverage.": "सहकारी कल्याण कवरेज।",
        "Workers with active protection": "सक्रिय सुरक्षा वाले कामगार",
        "Demand intelligence": "मांग की जानकारी",
        "Use recent demand to plan worker capacity for the next 7 days.": "अगले 7 दिनों के लिए कामगार क्षमता की योजना बनाने हेतु हाल की मांग का उपयोग करें।",
        "Predictive MVP": "पूर्वानुमान MVP",
        "Recent operations": "हाल के संचालन",
        "Latest booking activity across the network.": "पूरे नेटवर्क की नवीनतम बुकिंग गतिविधि।",
        "No bookings yet.": "अभी कोई बुकिंग नहीं है।",

        /* Common */
        "Experience": "अनुभव",
        "Certification": "प्रमाणपत्र",
        "Phone": "फ़ोन",
        "Skill": "कौशल",
        "Address": "पता",
        "Amount": "राशि",
        "Time": "समय",
        "Status": "स्थिति",
        "Provider": "सेवा प्रदाता",
        "Open document": "दस्तावेज़ खोलें",
        "No verification document uploaded": "कोई सत्यापन दस्तावेज़ अपलोड नहीं किया गया",
        "Reviewer note": "समीक्षक नोट",
        "Approve worker": "कामगार को मंज़ूरी दें",
        "Reject / request changes": "अस्वीकार करें / बदलाव मांगें",
        "Verification review": "सत्यापन समीक्षा",
        "Review the worker profile before granting trusted-booking access.": "भरोसेमंद बुकिंग की अनुमति देने से पहले कामगार प्रोफ़ाइल की समीक्षा करें।",

        /* Live tracking */
        "Worker is on the way": "कामगार रास्ते में है",
        "is travelling to your location.": "आपकी लोकेशन की ओर आ रहा है।",
        "Live": "लाइव",
        "Distance": "दूरी",
        "Approx ETA": "अनुमानित समय",
        "Location status": "लोकेशन स्थिति",
        "Connecting...": "कनेक्ट हो रहा है...",
        "Waiting for GPS...": "GPS की प्रतीक्षा...",
        "Waiting for worker GPS": "कामगार GPS की प्रतीक्षा",
        "Live • Updated just now": "लाइव • अभी अपडेट हुआ",
        "Reconnecting...": "दोबारा कनेक्ट हो रहा है...",
        "Tracking ended": "ट्रैकिंग समाप्त",
        "Worker": "कामगार",
        "Your location": "आपकी लोकेशन",
        "Live direction": "लाइव दिशा",
        "Waiting for first live location...": "पहली लाइव लोकेशन की प्रतीक्षा...",
        "Live worker location": "कामगार की लाइव लोकेशन",
        "Location updated recently.": "लोकेशन हाल ही में अपडेट हुई है.",

        /* Alerts */
        "Location is not supported by this browser.": "इस ब्राउज़र में लोकेशन सुविधा उपलब्ध नहीं है।",
        "Please allow location access to enable smart matching.": "स्मार्ट मिलान चालू करने के लिए लोकेशन की अनुमति दें।",
        "Please allow location access.": "कृपया लोकेशन की अनुमति दें।",
        "Location captured": "लोकेशन प्राप्त हो गई",
        "Expired": "समाप्त",

        /* Footer */
        "Platform": "प्लेटफ़ॉर्म",
        "Services": "सेवाएं",
        "How it works": "यह कैसे काम करता है",
        "Join Sahyog": "सहयोग से जुड़ें",
        "Worker login": "कामगार लॉगिन",
        "Benefits": "लाभ",
        "Trust": "भरोसा",
        "Verification": "सत्यापन",
        "Worker welfare": "कामगार कल्याण",
        "Community": "समुदाय",
        "Built for community empowerment.": "समुदाय के सशक्तिकरण के लिए निर्मित।",
        "A cooperative-owned service network connecting communities with trusted local workers.": "एक सहकारी-स्वामित्व वाला सेवा नेटवर्क जो समुदायों को भरोसेमंद स्थानीय कामगारों से जोड़ता है।",
        "Cooperative-owned · Verified local network": "सहकारी-स्वामित्व · सत्यापित स्थानीय नेटवर्क"
      },


      bn: {

        /* Navigation */
        "Home": "হোম",
        "Find Workers": "কর্মী খুঁজুন",
        "Find workers": "কর্মী খুঁজুন",
        "Dashboard": "ড্যাশবোর্ড",
        "Cooperative": "সমবায়",
        "Logout": "লগ আউট",
        "Login": "লগইন",
        "Get Started": "শুরু করুন",
        "Profile": "প্রোফাইল",
        "My Profile": "আমার প্রোফাইল",
        "My Services": "আমার পরিষেবা",
        "My Dashboard": "আমার ড্যাশবোর্ড",
        "My Bookings": "আমার বুকিং",
        "Worker Dashboard": "কর্মী ড্যাশবোর্ড",
        "Welfare": "কল্যাণ",
        "Welfare & Protection": "কল্যাণ ও সুরক্ষা",
        "Cooperative Control Center": "সমবায় নিয়ন্ত্রণ কেন্দ্র",
        "Django Admin": "জ্যাঙ্গো অ্যাডমিন",

        /* Customer dashboard */
        "Customer workspace": "গ্রাহক কর্মক্ষেত্র",
        "What's the work you need help with,": "আপনার কোন কাজে সাহায্য দরকার,",
        "Book trusted local help and keep every job in one place.": "বিশ্বস্ত স্থানীয় সাহায্য বুক করুন এবং সব কাজ এক জায়গায় রাখুন।",
        "Find a worker": "একজন কর্মী খুঁজুন",
        "All bookings": "সমস্ত বুকিং",
        "Total bookings": "মোট বুকিং",
        "Awaiting worker": "কর্মীর অপেক্ষায়",
        "Active jobs": "সক্রিয় কাজ",
        "Completed": "সম্পন্ন",
        "Recent bookings": "সাম্প্রতিক বুকিং",
        "Track your service requests.": "আপনার পরিষেবা অনুরোধ ট্র্যাক করুন।",
        "Emergency": "জরুরি",
        "Rate": "রেটিং দিন",
        "Pay": "পেমেন্ট করুন",
        "Invoice": "চালান",
        "No bookings yet.": "এখনও কোনো বুকিং নেই।",
        "Find a trusted worker and make your first booking.": "একজন বিশ্বস্ত কর্মী খুঁজে আপনার প্রথম বুকিং করুন।",
        "Browse services": "পরিষেবা দেখুন",
        "Need help fast?": "দ্রুত সাহায্য দরকার?",
        "Emergency requests are prioritized.": "জরুরি অনুরোধকে অগ্রাধিকার দেওয়া হয়।",
        "Choose a service, allow location and use the emergency workflow to send a priority request.": "একটি পরিষেবা বেছে নিন, লোকেশনের অনুমতি দিন এবং অগ্রাধিকার অনুরোধ পাঠাতে জরুরি প্রক্রিয়া ব্যবহার করুন।",
        "Find emergency-ready worker": "জরুরি পরিষেবার কর্মী খুঁজুন",
        "Only verified providers can receive new bookings.": "শুধুমাত্র যাচাইকৃত পরিষেবা প্রদানকারীরা নতুন বুকিং পেতে পারেন।",

        /* Worker dashboard */
        "Worker workspace": "কর্মী কর্মক্ষেত্র",
        "Build your local reputation.": "আপনার স্থানীয় সুনাম তৈরি করুন।",
        "Manage requests, services, earnings and your verification status.": "অনুরোধ, পরিষেবা, আয় এবং যাচাইকরণ অবস্থা পরিচালনা করুন।",
        "Add service": "পরিষেবা যোগ করুন",
        "Active bookings": "সক্রিয় বুকিং",
        "Completed jobs": "সম্পন্ন কাজ",
        "Worker rating": "কর্মীর রেটিং",
        "Completed value": "সম্পন্ন কাজের মূল্য",
        "Booking requests": "বুকিং অনুরোধ",
        "Accept only when you can deliver the job.": "আপনি কাজটি সম্পূর্ণ করতে পারলেই গ্রহণ করুন।",
        "Accept": "গ্রহণ করুন",
        "Reject": "প্রত্যাখ্যান করুন",
        "No new requests.": "কোনো নতুন অনুরোধ নেই।",
        "New customer requests will appear here.": "নতুন গ্রাহক অনুরোধ এখানে দেখা যাবে।",
        "Quick actions": "দ্রুত কাজ",
        "Keep your profile job-ready.": "আপনার প্রোফাইল কাজের জন্য প্রস্তুত রাখুন।",
        "Your jobs": "আপনার কাজ",
        "Use the workflow to move accepted jobs forward.": "গৃহীত কাজ এগিয়ে নিতে এই প্রক্রিয়া ব্যবহার করুন।",
        "On the Way": "পথে",
        "Arrived": "পৌঁছে গেছেন",
        "Start": "শুরু করুন",
        "Complete": "সম্পন্ন করুন",
        "No jobs yet.": "এখনও কোনো কাজ নেই।",

        /* Verification */
        "Verified worker": "যাচাইকৃত কর্মী",
        "Verification": "যাচাইকরণ",
        "under review": "পর্যালোচনাধীন",
        "needed": "প্রয়োজন",
        "Your profile can receive trusted bookings.": "আপনার প্রোফাইল বিশ্বস্ত বুকিং পেতে পারে।",
        "Submit a document/certification from your profile so the cooperative can review you.": "সমবায়ের পর্যালোচনার জন্য আপনার প্রোফাইল থেকে একটি নথি বা সার্টিফিকেট জমা দিন।",
        "View profile": "প্রোফাইল দেখুন",
        "Complete verification": "যাচাইকরণ সম্পূর্ণ করুন",

        /* Marketplace */
        "Marketplace": "পরিষেবা বাজার",
        "Find trusted local help.": "বিশ্বস্ত স্থানীয় সাহায্য খুঁজুন।",
        "Verified providers, clear pricing and smart matching.": "যাচাইকৃত প্রদানকারী, স্পষ্ট মূল্য এবং স্মার্ট ম্যাচিং।",
        "Use my location": "আমার লোকেশন ব্যবহার করুন",
        "All categories": "সব বিভাগ",
        "Search": "খুঁজুন",
        "Smart matching enabled — results are ranked by proximity and worker trust signals.": "স্মার্ট ম্যাচিং চালু — দূরত্ব এবং কর্মীর বিশ্বাসযোগ্যতার ভিত্তিতে ফলাফল সাজানো হয়েছে।",
        "services available": "পরিষেবা উপলব্ধ",
        "Verified providers are prioritized": "যাচাইকৃত প্রদানকারীদের অগ্রাধিকার দেওয়া হয়",
        "Verified": "যাচাইকৃত",
        "Verification pending": "যাচাইকরণ অপেক্ষমাণ",
        "Starting from": "শুরু হচ্ছে",
        "Book": "বুক করুন",
        "Not bookable": "বুক করা যাবে না",
        "No matching services": "কোনো মিল থাকা পরিষেবা পাওয়া যায়নি",
        "Try another category or search term.": "অন্য বিভাগ বা অনুসন্ধান শব্দ চেষ্টা করুন।",

        /* Booking */
        "Back to services": "পরিষেবায় ফিরে যান",
        "Booking request": "বুকিং অনুরোধ",
        "Emergency request": "জরুরি অনুরোধ",
        "We’ll prioritize this booking with the verified worker network.": "যাচাইকৃত কর্মী নেটওয়ার্ক এই বুকিংকে অগ্রাধিকার দেবে।",
        "Service address": "পরিষেবার ঠিকানা",
        "Date": "তারিখ",
        "Preferred time": "পছন্দের সময়",
        "Use my current location": "আমার বর্তমান লোকেশন ব্যবহার করুন",
        "Your location is used only to improve worker matching.": "আপনার লোকেশন শুধুমাত্র কর্মী ম্যাচিং উন্নত করতে ব্যবহার করা হয়।",
        "Confirm Booking Request": "বুকিং অনুরোধ নিশ্চিত করুন",
        "Send Emergency Request": "জরুরি অনুরোধ পাঠান",

        /* Payment */
        "Choose Payment Method": "পেমেন্টের পদ্ধতি বেছে নিন",
        "Online / UPI": "অনলাইন / UPI",
        "Cash": "নগদ",
        "Payment": "পেমেন্ট",

        /* Invoice */
        "Service invoice": "পরিষেবা চালান",
        "Customer": "গ্রাহক",
        "Provider": "পরিষেবা প্রদানকারী",
        "Service subtotal": "পরিষেবার উপ-মোট",
        "Cooperative platform fee (5%)": "সমবায় প্ল্যাটফর্ম ফি (৫%)",
        "Total": "মোট",
        "Worker earnings after platform fee:": "প্ল্যাটফর্ম ফি-এর পর কর্মীর আয়:",
        "Payment status:": "পেমেন্টের অবস্থা:",
        "Print / Save": "প্রিন্ট / সেভ",

        /* Dynamic billing */
        "Dynamic Billing": "ডায়নামিক বিলিং",
        "Base": "মূল মূল্য",
        "Base service": "মূল পরিষেবা মূল্য",
        "Emergency fee": "জরুরি ফি",
        "Approved extras": "অনুমোদিত অতিরিক্ত",
        "Final amount": "চূড়ান্ত মূল্য",
        "Final payable": "চূড়ান্ত প্রদেয়",
        "Extra charges": "অতিরিক্ত চার্জ",
        "Parts / Material": "পার্টস / উপকরণ",
        "Additional Labour": "অতিরিক্ত শ্রম",
        "Additional Service": "অতিরিক্ত পরিষেবা",
        "Other": "অন্যান্য",
        "Description": "বিবরণ",
        "Quantity": "পরিমাণ",
        "Unit price": "প্রতি ইউনিট মূল্য",
        "Unit Price": "প্রতি ইউনিট মূল্য",
        "Total": "মোট",
        "Awaiting Customer Approval": "গ্রাহকের অনুমোদনের অপেক্ষায়",
        "Approved": "অনুমোদিত",
        "Rejected": "প্রত্যাখ্যাত",
        "Add charge": "চার্জ যোগ করুন",
        "Add Extra Charge": "অতিরিক্ত চার্জ যোগ করুন",
        "Customer approval required": "গ্রাহকের অনুমোদন প্রয়োজন",
        "Approve": "অনুমোদন করুন",
        "Reject": "প্রত্যাখ্যান করুন",
        "Customer note": "গ্রাহকের নোট",
        "Optional note": "ঐচ্ছিক নোট",

        /* Welfare */
        "Worker protection": "কর্মী সুরক্ষা",
        "Welfare & insurance": "কল্যাণ ও বীমা",
        "Build a stronger safety net through the cooperative.": "সমবায়ের মাধ্যমে একটি শক্তিশালী নিরাপত্তা ব্যবস্থা তৈরি করুন।",
        "Current plan": "বর্তমান পরিকল্পনা",
        "Coverage": "কভারেজ",
        "Monthly contribution": "মাসিক অবদান",
        "Protection plan": "সুরক্ষা পরিকল্পনা",
        "Enroll me in the cooperative welfare plan": "আমাকে সমবায় কল্যাণ পরিকল্পনায় যুক্ত করুন",
        "Keep emergency support enabled": "জরুরি সহায়তা চালু রাখুন",
        "Notes": "নোট",
        "Save welfare preferences": "কল্যাণ পছন্দ সংরক্ষণ করুন",
        "Protected": "সুরক্ষিত",
        "Setup needed": "সেটআপ প্রয়োজন",

        /* Admin */
        "Cooperative control center": "সমবায় নিয়ন্ত্রণ কেন্দ্র",
        "Run the network.": "নেটওয়ার্ক পরিচালনা করুন।",
        "Trust, operations, payments, worker welfare and demand intelligence in one place.": "বিশ্বাস, পরিচালনা, পেমেন্ট, কর্মী কল্যাণ এবং চাহিদার তথ্য এক জায়গায়।",
        "Admin": "অ্যাডমিন",
        "View platform": "প্ল্যাটফর্ম দেখুন",
        "Workers": "কর্মীরা",
        "Bookings": "বুকিং",
        "Network volume": "নেটওয়ার্ক কার্যক্রম",
        "Verified revenue": "যাচাইকৃত রাজস্ব",
        "Payment ledger": "পেমেন্ট লেজার",
        "Needs attention": "মনোযোগ প্রয়োজন",
        "Verification queue": "যাচাইকরণ তালিকা",
        "Review workers waiting for cooperative approval.": "সমবায়ের অনুমোদনের অপেক্ষায় থাকা কর্মীদের পর্যালোচনা করুন।",
        "Review": "পর্যালোচনা করুন",
        "Verification queue is clear.": "যাচাইকরণ তালিকা খালি।",
        "Network pulse": "নেটওয়ার্ক কার্যক্রম",
        "Last 30 days of booking activity.": "গত ৩০ দিনের বুকিং কার্যক্রম।",
        "Payment review": "পেমেন্ট পর্যালোচনা",
        "Verify customer UPI submissions before marking the ledger paid.": "লেজারে পেমেন্ট সম্পন্ন চিহ্নিত করার আগে গ্রাহকের UPI পেমেন্ট যাচাই করুন।",
        "Verify": "যাচাই করুন",
        "No payment submissions yet.": "এখনও কোনো পেমেন্ট জমা হয়নি।",
        "Workers with active protection": "সক্রিয় সুরক্ষা থাকা কর্মী",
        "Demand intelligence": "চাহিদার তথ্য",
        "Use recent demand to plan worker capacity for the next 7 days.": "পরবর্তী ৭ দিনের কর্মী ক্ষমতার পরিকল্পনার জন্য সাম্প্রতিক চাহিদা ব্যবহার করুন।",
        "Predictive MVP": "পূর্বাভাস MVP",
        "Recent operations": "সাম্প্রতিক কার্যক্রম",
        "Latest booking activity across the network.": "পুরো নেটওয়ার্কের সর্বশেষ বুকিং কার্যক্রম।",
        "No bookings yet.": "এখনও কোনো বুকিং নেই।",

        /* Common */
        "Experience": "অভিজ্ঞতা",
        "Certification": "সার্টিফিকেট",
        "Phone": "ফোন",
        "Skill": "দক্ষতা",
        "Address": "ঠিকানা",
        "Amount": "পরিমাণ",
        "Time": "সময়",
        "Status": "অবস্থা",
        "Open document": "নথি খুলুন",
        "No verification document uploaded": "কোনো যাচাইকরণ নথি আপলোড করা হয়নি",
        "Reviewer note": "পর্যালোচকের নোট",
        "Approve worker": "কর্মী অনুমোদন করুন",
        "Reject / request changes": "প্রত্যাখ্যান / পরিবর্তন অনুরোধ করুন",
        "Verification review": "যাচাইকরণ পর্যালোচনা",
        "Review the worker profile before granting trusted-booking access.": "বিশ্বস্ত বুকিংয়ের অনুমতি দেওয়ার আগে কর্মীর প্রোফাইল পর্যালোচনা করুন।",

        /* Live tracking */
        "Worker is on the way": "কর্মী পথে রয়েছেন",
        "is travelling to your location.": "আপনার লোকেশনের দিকে আসছেন।",
        "Live": "লাইভ",
        "Distance": "দূরত্ব",
        "Approx ETA": "আনুমানিক সময়",
        "Location status": "লোকেশনের অবস্থা",
        "Connecting...": "সংযোগ হচ্ছে...",
        "Waiting for GPS...": "GPS-এর অপেক্ষায়...",
        "Waiting for worker GPS": "কর্মীর GPS-এর অপেক্ষায়",
        "Live • Updated just now": "লাইভ • এইমাত্র আপডেট হয়েছে",
        "Reconnecting...": "পুনরায় সংযোগ হচ্ছে...",
        "Tracking ended": "ট্র্যাকিং শেষ",
        "Worker": "কর্মী",
        "Your location": "আপনার লোকেশন",
        "Live direction": "লাইভ দিক",
        "Waiting for first live location...": "প্রথম লাইভ লোকেশনের অপেক্ষায়...",
        "Live worker location": "কর্মীর লাইভ লোকেশন",
        "Location updated recently.": "লোকেশন সম্প্রতি আপডেট হয়েছে।",

        /* Alerts */
        "Location is not supported by this browser.": "এই ব্রাউজারে লোকেশন সুবিধা সমর্থিত নয়।",
        "Please allow location access to enable smart matching.": "স্মার্ট ম্যাচিং চালু করতে লোকেশন ব্যবহারের অনুমতি দিন।",
        "Please allow location access.": "অনুগ্রহ করে লোকেশন ব্যবহারের অনুমতি দিন।",
        "Location captured": "লোকেশন পাওয়া গেছে",
        "Expired": "মেয়াদ শেষ",

        /* Footer */
        "Platform": "প্ল্যাটফর্ম",
        "Services": "পরিষেবা",
        "How it works": "এটি কীভাবে কাজ করে",
        "Join Sahyog": "সহযোগে যোগ দিন",
        "Worker login": "কর্মী লগইন",
        "Benefits": "সুবিধা",
        "Trust": "বিশ্বাস",
        "Verification": "যাচাইকরণ",
        "Worker welfare": "কর্মী কল্যাণ",
        "Community": "সম্প্রদায়",
        "Built for community empowerment.": "সম্প্রদায়ের ক্ষমতায়নের জন্য তৈরি।",
        "A cooperative-owned service network connecting communities with trusted local workers.": "একটি সমবায়-মালিকানাধীন পরিষেবা নেটওয়ার্ক যা সম্প্রদায়কে বিশ্বস্ত স্থানীয় কর্মীদের সাথে যুক্ত করে।",
        "Cooperative-owned · Verified local network": "সমবায়-মালিকানাধীন · যাচাইকৃত স্থানীয় নেটওয়ার্ক"

      }

    };


    const dictionary =
      translations[language] || {};


    /*
     * Translate text while preserving whitespace.
     */
    function translateText(text) {

      if (!text || !text.trim()) {
        return text;
      }


      let result = text;


      const trimmed =
        result.trim();


      /*
       * Exact translation first.
       */
      if (dictionary[trimmed]) {

        const translated =
          dictionary[trimmed];

        return result.replace(
          trimmed,
          translated
        );

      }


      /*
       * Partial translation.
       * Longest strings first so that a short word
       * doesn't replace part of a longer sentence.
       */
      const keys =
        Object.keys(dictionary)
          .sort(
            (a, b) =>
              b.length - a.length
          );


      keys.forEach(
        function (key) {

          if (
            result.includes(key)
          ) {

            result =
              result.replaceAll(
                key,
                dictionary[key]
              );

          }

        }
      );


      return result;

    }


    /*
     * Translate all visible text nodes.
     */
    function translateTextNodes(root) {

      const walker =
        document.createTreeWalker(
          root,
          NodeFilter.SHOW_TEXT,
          {
            acceptNode: function (node) {

              /*
               * Ignore scripts, styles and map internals.
               */
              const parent =
                node.parentElement;

              if (!parent) {
                return NodeFilter.FILTER_REJECT;
              }


              const tag =
                parent.tagName.toLowerCase();


              if (
                tag === "script" ||
                tag === "style" ||
                tag === "noscript"
              ) {

                return NodeFilter.FILTER_REJECT;

              }


              return NodeFilter.FILTER_ACCEPT;

            }
          }
        );


      const nodes = [];


      let node;


      while (
        (node = walker.nextNode())
      ) {

        nodes.push(node);

      }


      nodes.forEach(
        function (textNode) {

          textNode.nodeValue =
            translateText(
              textNode.nodeValue
            );

        }
      );

    }


    /*
     * Translate useful HTML attributes.
     */
    function translateAttributes() {

      const attributes = [
        "placeholder",
        "title",
        "aria-label",
        "data-bs-original-title"
      ];


      document
        .querySelectorAll("*")
        .forEach(
          function (element) {

            attributes.forEach(
              function (attribute) {

                if (
                  element.hasAttribute(
                    attribute
                  )
                ) {

                  const value =
                    element.getAttribute(
                      attribute
                    );


                  const translated =
                    translateText(
                      value
                    );


                  if (
                    translated !== value
                  ) {

                    element.setAttribute(
                      attribute,
                      translated
                    );

                  }

                }

              }
            );

          }
        );

    }


    /*
     * Translate document title.
     */
    function translateDocumentTitle() {

      const title =
        document.title;


      const translated =
        translateText(
          title
        );


      if (
        translated !== title
      ) {

        document.title =
          translated;

      }

    }


    /*
     * Run translation after Django has
     * finished rendering the page.
     */
    translateTextNodes(
      document.body
    );

    translateAttributes();

    translateDocumentTitle();


    /*
     * Some dashboard elements can change
     * after page load. Observe them and translate
     * only newly inserted content.
     */
    const observer =
      new MutationObserver(
        function (mutations) {

          mutations.forEach(
            function (mutation) {

              mutation.addedNodes.forEach(
                function (node) {

                  if (
                    node.nodeType ===
                    Node.TEXT_NODE
                  ) {

                    node.nodeValue =
                      translateText(
                        node.nodeValue
                      );

                  } else if (
                    node.nodeType ===
                    Node.ELEMENT_NODE
                  ) {

                    translateTextNodes(
                      node
                    );

                    translateAttributes();

                  }

                }
              );

            }
          );

        }
      );


    observer.observe(
      document.body,
      {
        childList: true,
        subtree: true
      }
    );

  }



  /*
   * Expose the translator for small UI messages generated by other
   * scripts/templates without changing their existing behavior.
   */
  window.sahyogTranslate = function (value) {
    if (language !== "hi" && language !== "bn") return value;
    return translateText(value);
  };

  /* =========================================================
     BOOKING REQUEST COUNTDOWN
     ========================================================= */

  document
    .querySelectorAll(
      "[data-request-timer]"
    )
    .forEach(
      el => {

        const deadline =
          new Date(
            el.dataset.requestTimer
          ).getTime();


        const tick = () => {

          const remaining =
            Math.max(
              0,
              Math.floor(
                (
                  deadline -
                  Date.now()
                ) / 1000
              )
            );


          const mm =
            String(
              Math.floor(
                remaining / 60
              )
            ).padStart(2, "0");


          const ss =
            String(
              remaining % 60
            ).padStart(2, "0");


          el.textContent =
            `${mm}:${ss}`;


          if (
            remaining <= 0
          ) {

            clearInterval(
              interval
            );


            el.textContent =
              "Expired";


            el.classList.add(
              "text-danger"
            );


            const row =
              el.closest(
                "[data-request-row]"
              );


            row
              ?.querySelectorAll(
                "form button"
              )
              .forEach(
                b =>
                  b.disabled = true
              );


            setTimeout(
              () =>
                window.location.reload(),
              1500
            );

          }

        };


        tick();


        const interval =
          setInterval(
            tick,
            1000
          );

      }
    );

});



/* =========================================================
   NAVIGATION DRAWER + LOCATION HELPERS
   ========================================================= */

document.addEventListener(
  "DOMContentLoaded",
  () => {

    const drawer =
      document.getElementById(
        "sideDrawer"
      );


    const overlay =
      document.getElementById(
        "drawerOverlay"
      );


    const trigger =
      document.getElementById(
        "drawerTrigger"
      );


    const close =
      document.getElementById(
        "drawerClose"
      );


    const setDrawer =
      (open) => {

        drawer?.classList.toggle(
          "show",
          open
        );


        overlay?.classList.toggle(
          "show",
          open
        );


        document.body.classList.toggle(
          "drawer-open",
          open
        );

      };


    trigger?.addEventListener(
      "click",
      () =>
        setDrawer(true)
    );


    close?.addEventListener(
      "click",
      () =>
        setDrawer(false)
    );


    overlay?.addEventListener(
      "click",
      () =>
        setDrawer(false)
    );


    document.addEventListener(
      "keydown",
      e => {

        if (
          e.key === "Escape"
        ) {

          setDrawer(false);

        }

      }
    );


    /*
     * Generic location forms.
     */
    document
      .querySelectorAll(
        "[data-locate-form]"
      )
      .forEach(
        btn => {

          btn.addEventListener(
            "click",
            () => {

              if (
                !navigator.geolocation
              ) {

                return alert(
                  window.sahyogTranslate?.("Location is not supported by this browser.") ||
                  "Location is not supported by this browser."
                );

              }


              navigator
                .geolocation
                .getCurrentPosition(

                  pos => {

                    const form =
                      document.querySelector(
                        btn.dataset.locateForm
                      );


                    if (!form) {
                      return;
                    }


                    form.querySelector(
                      '[name="lat"]'
                    ).value =
                      pos.coords.latitude;


                    form.querySelector(
                      '[name="lng"]'
                    ).value =
                      pos.coords.longitude;


                    form.submit();

                  },


                  () =>
                    alert(
                      window.sahyogTranslate?.("Please allow location access to enable smart matching.") ||
                      "Please allow location access to enable smart matching."
                    )

                );

            }
          );

        }
      );


    /*
     * Current location buttons.
     */
    document
      .querySelectorAll(
        "[data-current-location]"
      )
      .forEach(
        btn => {

          btn.addEventListener(
            "click",
            () => {

              if (
                !navigator.geolocation
              ) {
                return;
              }


              navigator
                .geolocation
                .getCurrentPosition(

                  pos => {

                    const lat =
                      document.querySelector(
                        '[name="latitude"]'
                      );


                    const lng =
                      document.querySelector(
                        '[name="longitude"]'
                      );


                    if (lat) {

                      lat.value =
                        pos.coords.latitude;

                    }


                    if (lng) {

                      lng.value =
                        pos.coords.longitude;

                    }


                    btn.innerHTML =
                      '<i class="bi bi-check-circle me-2"></i>Location captured';


                    btn.classList.add(
                      "btn-success"
                    );

                  },


                  () =>
                    alert(
                      window.sahyogTranslate?.("Please allow location access.") ||
                      "Please allow location access."
                    )

                );

            }
          );

        }
      );

  }
);