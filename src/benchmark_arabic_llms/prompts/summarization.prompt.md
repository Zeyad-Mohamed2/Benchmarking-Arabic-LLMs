You are an expert Arabic text summarization specialist trained to generate clear, concise, and informative summaries in Modern Standard Arabic.

## Context
Your task is to create high-quality summaries that capture the essential information from Arabic text while discarding unnecessary details and maintaining coherence.

---

## Text to Summarize
"""
{text}
"""

---

## Instructions

Follow these steps systematically:

1. **Read and Comprehend**: Read the entire text carefully to understand its main topic, key points, and overall message.

2. **Identify Core Information**: 
   - Identify the main topic or event
   - Extract key facts, dates, names, and numbers
   - Recognize the most important information that answers: Who, What, When, Where, Why, How

3. **Discard Non-Essential Details**:
   - Remove redundant information and repetitions
   - Eliminate filler words and unnecessary elaborations
   - Skip minor details that don't contribute to the main message
   - Avoid tangential or secondary information

4. **Synthesize**: Combine the essential information into a coherent, flowing summary.

5. **Write Your Summary**: 
   - Use clear, grammatically correct Modern Standard Arabic (MSA)
   - Write EXACTLY 1-3 sentences (strictly enforce this limit)
   - Ensure the summary is self-contained and understandable without the original
   - Maintain objectivity - no opinions or interpretations

6. **Verify**: Before submitting, check that your summary:
   - ✓ Contains ONLY information from the original text
   - ✓ Is written in Modern Standard Arabic (MSA)
   - ✓ Is between 1-3 sentences (no more, no less)
   - ✓ Captures the most important information
   - ✓ Is grammatically correct and coherent
   - ✓ Contains no repetitions or redundancies

---

## Critical Constraints

- ✓ Write in Modern Standard Arabic (MSA) exclusively
- ✓ Maximum 3 sentences - strictly enforce this limit
- ✓ Include ONLY essential information (main ideas, key facts)
- ✓ Maintain objectivity and neutrality
- ✓ Ensure grammatical correctness and natural flow
- ✓ Preserve critical details: names, dates, numbers, locations
- ✗ Do NOT exceed 3 sentences under any circumstances
- ✗ Do NOT add information not present in the original
- ✗ Do NOT include opinions, interpretations, or analysis
- ✗ Do NOT repeat information
- ✗ Do NOT use filler words or unnecessary elaborations

---

## Examples

**Example 1 - News Article:**

Input text:
"احرز الفيلم التونسي هكه خير جائزه المهر البرونزي ضمن مشاركته الدوره للمهرجان الافريقي للسينما التلفزه فسباكو العاصمه البوركينيه واغادوغو مخرج الفيلم مهدي البرصاوي ضيف سينما سينما فيلمه نجح اقتلاع جائزه فيلم قصير مشارك المهرجان منتقدا اعتبره سوء تنظيم خلال عرض الافلام المشاركه اشاد الوقت بتمكين التلاميذ غياب استثنائي الدروس السماح بحضور فعاليات المهرجان مشاهده الافلام المشاركه داعيا القائمين المهرجانات السينمائيه تونس للاقتداء بهذه التجربه تشجيعا للناشئه متابعه السينما اضاف البرصاوي فيلمه هكه خير سيكون ضمن المشاركين مهرجانات عالميه الاسبوع القادم خلال الفتره الاقصر بيروت امستردام جنيف البرصاوي فيلمه قاعات السينما بتونس العاصمه ابتداء يوم الحالي اطار تظاهره الخاصه بالافلام القصيره يستبعد عرضه قريبا باقي ولايات الجمهوريه"

Good summary:
"أحرز الفيلم التونسي "خليّنا هكة خير" على جائزة المهر البرونزي ضمن مشاركته في الدورة 25 للمهرجان الإفريقي للسينما و التلفزة "فسباكو" الذي نُظم في العاصمة البوركينية واغادوغو."

Reason: Captures the essential information (film name, award, festival, location) in one clear sentence, eliminating all secondary details about the director's opinions and future plans.

**Example 2 - Cultural Event:**

Input text:
"اشرف رئيس الجمهوريه الباجي قايد السبسي اليوم بقصر قرطاج موكب منح الوسام الوطني للاستحقاق الثقافي الفنانين والمبدعين بمناسبه انعقاد ايام قرطاج السينمائيه والفنانون الصنف عبد الرحمان سيساكو موريتانيا جميل راتب مصر ميشال خليفي فلسطين ادريسا ودراغو بوركينا فاسو محمد ملص سوريا رضا الباهي تونس الحضور عمر الخليفي تونس الصنف الثاني عبد العزيز بن ملوكه تونس نجيب تونس منصف شرف الدين تونس الحضور الصنف الثالث ابراهيم تونس الخياطي تونس الحضور تونس عليها الحضور شوقي الماجري تونس الصنف الرابع كوثر بن تونس"

Good summary:
"أشرف رئيس الجمهورية الباجي قايد السبسي اليوم بقصر قرطاج على موكب منح الوسام الوطني للاستحقاق الثقافي لثلّة من الفنانين والمبدعين و ذلك بمناسبة انعقاد أيام قرطاج السينمائية."

Reason: Summarizes the main event (award ceremony, who, where, why) without listing all individual recipients, which is secondary information.

**Example 3 - Technology News:**

Input text:
"تستعد شركه سامسونغ للاعلان قريبا السبب الحقيقي لانفجار هواتف غالاكسي نوت كشفته مصادر مقربه المجموعه واكد خبراء الشركه ستعلن يوم الاثنين السبب الحقيقي لانفجار هواتف نوت الاخيره وسيتزامن الاعلان طرح النتائج الماليه حققتها سامسونغ الربع الاخير عام وترجح الاحتمالات القائمه حاليا سبب انفجار الهواتف يعود تسرع الشركه انتاجها وطرحها الاسواق اضافه انشغال الخبراء بمشروع انتاج هاتف غالاكسي S المصادر ذاتها وكانت تجربه انتاج هواتف غالاكسي نوت سيئه نوعا وجهه نظر الخبراء داخل الشركه ولكنها دفعتهم للتفكير بشكل افضل واخذ الوقت اللازم للتحقق التفاصيل طرح هاتف تلافيا لاي مشاكل تعود بنتائج كارثيه الشركه مستقبلا"

Good summary:
"تستعد شركة سامسونغ للإعلان قريبا عن السبب الحقيقي لإنفجار هواتف "غالاكسي نوت-7" حسب ما كشفته مصادر مقربة من المجموعة."

Reason: Focuses on the main news (Samsung announcement about phone explosions) without speculation or internal details.

**Example 4 - Political/Diplomatic:**

Input text:
"تعمل الاتفاقية على تعميق العلاقات بين فيتنام والاتحاد الأوروبي وتم اعتمادها بموجب قرار المجلس (الاتحاد الأوروبي) 2020/753 المؤرخ 30 مارس 2020 بشأن إبرام اتفاقية التجارة الحرة بين الاتحاد الأوروبي وفيتنام. تم تمرير الاتفاقية في فيتنام في 8 يونيو 2020 في الجمعية الوطنية الفيتنامية ودخلت حيز التنفيذ في 1 أغسطس من ذلك العام. تمت الموافقة على كلا الاتفاقيتين من قبل المشرعين الفيتناميين بأغلبية كبيرة بلغت حوالي 95٪ من الأصوات."

Good summary:
"دخلت اتفاقية التجارة الحرة بين الاتحاد الأوروبي وفيتنام حيز التنفيذ في 1 أغسطس 2020 بعد موافقة المشرعين الفيتناميين عليها بأغلبية 95٪."

Reason: Combines the essential facts (agreement type, parties, date, approval rate) in a single concise sentence.

**Example 5 - Sports/Entertainment:**

Input text:
"انطلقت فعاليات التظاهره الموسيقيه الالكترونيه صوت الصحراء Sounds Sahara دورتها الثانيه بمدينه توزر يومين وقال مدير التظاهره سامي مهني مداخله الجوهره اف ام اليوم الدوره تنطلق يوم مدى يومين ستشهد تغييرات هامه مستوى الديكورات ومستوى الحضور الكبير لفنانين عالميين المانيا واضاف التنسيق لهذه التظاهره تم بالشراكه وزاره السياحه قامت بتوجيه الدعوه لعدد كبير الاعلاميين الاجانب غرار التونسيين لحضور التظاهره والتسويق لصوره تونس الخارج لتشجيع السياحه قوله"

Good summary:
"تنطلق فعاليات التظاهرة الموسيقية الالكترونية صوت الصحراء "Sounds of Sahara"، في دورتها الثانية بمدينة توزر بعد يومين."

Reason: Focuses on the core announcement (event name, edition, location, timing) without director quotes or partnership details.

---

## Your Summary

Summary: