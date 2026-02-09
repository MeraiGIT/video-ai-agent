THis is what I want for this app, it should be an ultimate production team that can generate anything ANYTHING, any video or photo content the user asked in the most professional way possible.

Step 1. User input - it can be anything, the user can give the agent a reference photo and ask to create any video with this character. Or a user can give a video and ask to recreate it. Or a user can give info about a youtube video he is planning and ask to create a lot of motion graphics for his video.

Step 2. the agent takes the user input and at the same time access all of the nodes (which represent the use of different image generation and video generation models from kie or fal ai). From the user input he  Parse the request into a universal project structure:       │
  │  - What is being created (video, image, film, ad, podcast)   │
  │  - Who is the audience                                       │
  │  - Where will it be published (platform + specs)             │
  │  - Reference materials (face photos, brand assets, examples) │
  │  - Constraints (duration, dimensions, style, budget)         │
  │                                                              │
  │  Output: Project { type, audience, platform, references,     │
  │          constraints }  - he gives his suggestions based on the user input but asks if he thinks to achive the best possible quality of the goal he needs some more info (like a production team interviews their clients) however, the user can still ask the agent to come up with something. Maybe it needs some more reference photos or something - it should be smart

  step 3. Then the agent thinks, based on the user input, to achieve the best quality possible, do I need to do a web search, if yes, then he does it. Web search + analysis tailored to the project:              │
  │  - What's performing well in this format/niche RIGHT NOW     │
  │  - Platform-specific best practices and specs                │
  │  - Competitor/reference analysis                             │
  │  - Trending styles, sounds, formats                          │
  │                                                              │
  │  Output: ResearchInsights { trends, references, specs,       │
  │          recommendations } 

  Step 3. Then based of the task and web search, and knowledge about which models for the pipeline are availble which ones are good for which tasks, how much does each of them cost and what each of them does - it drives into a creative direction plan. The brain of the system. One sophisticated LLM call that    │
  │  takes project + research and outputs a COMPLETE creative    │
  │  brief + production plan:                                    │
  │                                                              │
  │  Creative Brief:                                             │
  │  - Concept & narrative approach                              │
  │  - Visual style (mood board description, color palette)      │
  │  - Tone & voice                                              │
  │  - Pacing & rhythm                                           │
  │  - Typography & text treatment (if applicable)               │
  │  - Audio direction (music mood, VO style, SFX approach)   
  and also, a production plan with Ordered list of production steps this project needs       │
  │  - Each step = a CAPABILITY from the shared layer            │
  │  - e.g. a poster needs: [image_gen, compositing, typography] │
  │  - e.g. a film needs: [script, storyboard, face_ref,        │
  │    image_gen x100, video_gen x100, voice, music, sfx,        │
  │    mix, assembly, captions, color_grade. However, the agent gives a rough budget estimate of the plan to produce and gives 3 variants. So for instance: we need to generate a viral tiktok video it gives the creative breaf with the format, adding captures, using eleven labs for audio, the vido needs some vfx. Then for this type of query I recommend to use the nano banana pro for image generation. Use veo 3.1 fast with first and last frame for video generation and also, generate the video with audio and then filter it through eleven labs to mimic the diologue in the video with the custom voice. Then assembly it with this type of transitions at each steps and create a collorful captions. Or a cheaper varient to use seedance 1.5 or kling 3.0 and so on if you understand what I am saying. The agent know the costs of the models, what they good at or bad which is best or worst and give the full pipeline to the user an intelligent one with budget choices and quality tradeoffs. Then the user either chat with it or approve.

  Step 4. The agent generate a blueprint using llm and previous inputs. 4. BLUEPRINT                             │
  │                                                              │
  │  Detailed execution plan based on creative brief:            │
  │                                                              │
  │  If video/film:                                              │
  │    Script (hook, narrative, CTA, timing markers)             │
  │    Scene-by-scene storyboard (visual, camera, motion,        │
  │    duration, transitions, text overlays)                     │
  │    Audio map (where music swells, SFX hits, VO pacing)       │
  │                                                              │
  │  If graphic/design:                                          │
  │    Layout wireframe (element positions, hierarchy)           │
  │    Element descriptions (each visual component)              │
  │    Typography plan (what text, where, what style)            │
  │                                                              │
  │  If audio/podcast:                                           │
  │    Script with speaker notes                                 │
  │    Segment breakdown with timing                             │
  │    Music/SFX cue sheet                                       │
  │                                                              │
  │  If long-form (film, documentary):                           │
  │    Chapter/act breakdown                                     │
  │    Per-chapter scene storyboards                             │
  │    Character consistency notes                               │
  │    Continuity plan         this should be a professional blueprint with best practices, a full one and should include the best methods for production and prompting of each model like we did in the v2 version of the app but we should make it better for each model, and this step should still go through llm because it shoudl not be a fixed pipeline but it should generate the best possible blueprint for any situation, any! then user review and approves the blueprint or chat and change.

  5. Production . The production goes according to the approved production plan. Executes the production_plan from step 3.                   │
  │  NOT hardcoded per content type — it walks through           │
  │  the plan and calls capabilities in order.                   │
  │                                                              │
  │  For a short video the plan might be:                        │
  │    face_ref → images(5) → videos(5) → voice → music → sfx   │
  │                                                              │
  │  For a 1-hour film:                                          │
  │    face_ref → FOR EACH CHAPTER:                              │
  │      images(N) → quality_gate → videos(N) → quality_gate    │
  │    → voice(full) → music(scored) → sfx → foley              │
  │                                                              │
  │  For a poster:                                               │
  │    images(elements) → composite → typography                 │
  │                                                              │
  │  For a podcast:                                              │
  │    voice(multi-speaker) → music_bed → sfx                    │
  │   and so on, it can be anything. However, at each step of the production plan it uses gemini 2.5 flash which analyzes each of the production output at each step and given the step 1-4 inputs decides - is it exceptional for what we asked for or not, if not it writes a brief of what is wrong in the generated content piece then send it to claude again and claude does this - it thinks what is the isuue, first it tries to regenerate content piece with a better prompt if then regenerates then again gemini flash analyzes (and this can be anything video, image or audio) it is not working it questions the model choose and proposes to user to switch the model to a better more expensive one. If in 2 tries the most expensive model does not give an exceptional result, the agent comes to user and says that and proposes to either keep the best of the not good enough variant or change something in step 1-4. This process happens in each step. So the agent generates, observes, think if it is good, if not regenerates or asks user permission to switch a model, if the generation is good gives it to the user for approval (but the final approval is at stage level not at per generation level - so it interfiers the user if needs approval to switch the model but it does not interfier to approve each of the generation), at this stage i need to generate 5 end frame based on the start fram generation earlier images - I generate 5 good ones then I ask user do we move on to the next stage? And this untill we go through all of the stages of the production pipeline.

  6.  6. ASSEMBLE                              │
  │                                                              │
  │  Combine all produced assets per blueprint:                  │
  │    Video: clips + transitions + audio sync                   │
  │    Film: chapters + scene transitions + continuity           │
  │    Graphic: layer compositing + final render                 │
  │    Audio: full mix + segment joins                           │
  │                                                              │
  │  follows the blueprint and production plan exactly. then gives to the user and askes for permision to move on as well as give the user its polish plans.

  7.   7. POLISH                               │
  │                                                              │
  │  Finishing touches driven by creative brief:                 │
  │    Captions/subtitles (styled per brief)                     │
  │    Color grading                                             │
  │    Audio normalization (platform loudness standards)          │
  │    Text overlays / watermarks                                │
  │    Thumbnail generation (for video content)                  │
  │    Credits (for long-form)                                   │
  │                                                              │
  │  follows brief + platform specs  and gives it to the user if approved moves forward.

  8. DELIVER                              │
  │                                                              │
  │  Platform-optimized export:                                  │
  │    Format, resolution, codec, aspect ratio                   │
  │    Platform metadata (title, description, hashtags)          │
  │    Thumbnail(s)                                              │
  │    Multiple variants if multi-platform                       │
  │                                                              │
  │  → USER REVIEWS final output 

  everything is saved in history as a folder for a project - the name of the project gets chosen by the llm. there in history - all of the materials generated filtered by each of the production and the discussed earlier pipelines (we need to think how to do it as every pipeline will be different). then the chat history button where we can click and it will send user to that chat in which the user can go and make more changes if he wants to.

  *** We need to think about the agentic graph structure, maybe we need to use one of this multi agent system patterns:
  Pattern 1: Sequential Pipeline
User → Researcher → Writer → Editor → END
Agents run in a fixed order, passing work to the next one. Simple but less flexible.

Pattern 2: Supervisor
User → Supervisor → (routes to) → Agent A or Agent B → back to Supervisor → END
A "boss" agent decides which specialist to call. More flexible, can loop back.

Pattern 3: Swarm (Peer-to-Peer)
[Agent A] ←→ [Agent B] ←→ [Agent C]
Agents hand off directly to each other
No central coordinator
Best for: Customer service flows

Pattern 4: Parallel
               ┌→ [Agent A] ─┐
User → Splitter ┼→ [Agent B] ─┼→ Combiner → END
                └→ [Agent C] ─┘
Multiple agents work simultaneously on different subtasks
Results are gathered and combined at the end
Best for: Research tasks, data gathering from multiple sources

Pattern 5: Communication (Message Board)
┌─────────────────────────────────────┐
│         SHARED MESSAGE BOARD        │
│  [Agent A posts] [Agent B reads]    │
│  [Agent B posts] [Agent C reads]    │
└─────────────────────────────────────┘
      ↑         ↑         ↑
   Agent A   Agent B   Agent C
***

***
For each of the nodes that will correspond to the use of models we should have a dedicated instruction which we will past to the llm which will explain what is this model, what it is good for, when to use, how much it costs, as well as best practices of prompting and others.
***

 