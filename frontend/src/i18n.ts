import i18n from "i18next";
import { initReactI18next } from "react-i18next";

// Botim markets: English / Arabic (RTL) / Hindi / Tagalog.
// Arabic is RTL — drives ConfigProvider direction + <html dir>.
export const RTL_LANGS = ["ar"];

const resources = {
  en: {
    translation: {
      app: "Botim Growth Console",
      nav: {
        audience: "Audience",
        campaign: "Campaign",
        analytics: "Analytics",
        personalization: "Personalization",
        content: "Content",
        experiment: "Experiment",
        data: "Data",
      },
      audience: {
        title: "Audience (Cohort Segmentation)",
        nl: "Describe your audience in plain language",
        translate: "Translate (NL2SQL)",
        estimate: "Estimate size",
        size: "Audience size",
        dsl: "Rule (DSL)",
        review: "Needs review",
      },
      campaign: {
        title: "Campaign",
        new: "New campaign",
        step_audience: "Target users",
        step_content: "Content (A/B/N)",
        step_schedule: "Schedule & goals",
        run: "Run",
      },
      common: { language: "Language", comingSoon: "Coming soon" },
    },
  },
  ar: {
    translation: {
      app: "منصة بوتيم للنمو",
      nav: {
        audience: "الجمهور",
        campaign: "الحملة",
        analytics: "التحليلات",
        personalization: "التخصيص",
        content: "المحتوى",
        experiment: "التجربة",
        data: "البيانات",
      },
      audience: {
        title: "الجمهور (تقسيم الشرائح)",
        nl: "صف جمهورك بلغة طبيعية",
        translate: "ترجمة (NL2SQL)",
        estimate: "تقدير الحجم",
        size: "حجم الجمهور",
        dsl: "القاعدة (DSL)",
        review: "يحتاج مراجعة",
      },
      campaign: {
        title: "الحملة",
        new: "حملة جديدة",
        step_audience: "المستخدمون المستهدفون",
        step_content: "المحتوى (A/B/N)",
        step_schedule: "الجدولة والأهداف",
        run: "تشغيل",
      },
      common: { language: "اللغة", comingSoon: "قريباً" },
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export function isRtl(lng: string): boolean {
  return RTL_LANGS.includes(lng);
}

export default i18n;
