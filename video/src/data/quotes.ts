// Verbatim quotes verified against the live catalog readers (site/read/…),
// from the translations the site uses: Qur'an = Saheeh International,
// hadith = Darussalam. Do not paraphrase — accuracy is the whole point.
export interface Quote {
  text: string;
  citation: string;
  translation: string;
  category: string;
}

export const QUOTES: Quote[] = [
  {
    text:
      "…advise them; [then if they persist], forsake them in bed; and [finally], strike them.",
    citation: "Qur'an 4:34",
    translation: "Saheeh International",
    category: "Women",
  },
  {
    text:
      "…married her when she was six years old and he consummated his marriage when she was nine years old.",
    citation: "Sahih al-Bukhari 5134",
    translation: "Darussalam",
    category: "Child Marriage",
  },
  {
    text: "Whoever changed his Islamic religion, then kill him.",
    citation: "Sahih al-Bukhari 6922",
    translation: "Darussalam",
    category: "Apostasy",
  },
];
