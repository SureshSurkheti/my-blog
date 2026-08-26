"""Content for the ``seed_kyushu`` management command.

Twelve travel posts covering all seven Kyushu prefectures, plus the Wikimedia
Commons file each one borrows its pictures from. ``fetch_seed_photos``
downloads the files listed here; ``seed_kyushu`` writes the posts.

The photographs are other people's work, published under free licences that
allow reuse with credit — so every seeded post ends with a credit list built
from the licence data Commons returns at download time. Swap in your own
photos and those credit lines can go.
"""

AUTHOR = {
    "first_name": "Suresh",
    "last_name": "Surkheti",
    "email_address": "suresh@gmail.com",
    "bio": (
        "Full-stack software engineer, writing from Oita in Kyushu. I have "
        "worked in Japanese IT since 2022. On weekends I take a train "
        "somewhere new and write down what I saw."
    ),
}

POSTS = [
    {
        "slug": "the-steaming-streets-of-beppu",
        "title": "The Steaming Streets of Beppu",
        "excerpt": (
            "My own town on a cold morning, when the whole valley looks like "
            "it is quietly boiling."
        ),
        "tags": ["Oita", "Onsen"],
        "published": "2025-01-18 09:20",
        "focal_point": "center",
        "image": "Beppu Umi-jigoku04n4272.jpg",
        "gallery": [
            ("Beppu City.jpg", "Steam coming straight off the street."),
            ("Beppu Chinoike-jigoku01n4272.jpg", "Chinoike Jigoku, the red one."),
            ("KannawaMushiyu.jpg", "The old steam bath house in Kannawa."),
        ],
        "content": """\
Beppu is the closest hot spring town to me, so I go there often. But in
January it feels like a different place. The air is cold, the ground is warm,
and white steam comes out of the hills, the drains and even the gaps between
houses. From the train you can see it before you see the town.

## The eight hells

The famous walk here is the *jigoku meguri*, the "hell tour". These are eight
hot springs that are too hot to bathe in. You only look at them.

My favourite is **Umi Jigoku**, the Sea Hell. The water is a strong blue,
almost like paint, and it is about 98 degrees. Standing next to it in winter
is very comfortable. Nearby is **Chinoike Jigoku**, the Blood Pond Hell, which
is deep red because of the iron in the clay.

A pass for all of them costs 2,200 yen. If you only have time for two, go to
Umi Jigoku and Chinoike Jigoku. They are the two that look nothing like the
others.

## Kannawa

Kannawa is the older part of town, up the hill. The streets are narrow and
steam comes straight out of the pipes at the side of the road. Small shops let
you cook eggs and vegetables in the steam. I did this once and it took about
ten minutes. The eggs tasted a little of sulphur, which I liked more than I
expected.

There is also a *mushiyu*, a steam bath, that has been used for hundreds of
years. You lie on a floor covered with a herb called *sekisho*. Ten minutes is
enough. I came out feeling like I had slept for a full night.

## A small tip

Do not try to see all eight hells in one afternoon. I did that on my first
visit and by the fifth one I stopped looking properly. Two or three, then a
long bath and a bowl of noodles, is a much better day.

## Getting there

From Oita Station it is about 15 minutes by train and costs 280 yen. The hells
are split into two areas, and a bus runs between them.
""",
    },
    {
        "slug": "a-slow-morning-in-yufuin",
        "title": "A Slow Morning in Yufuin",
        "excerpt": (
            "A small hot spring town under a twin-peaked mountain, best seen "
            "before the tour buses arrive."
        ),
        "tags": ["Oita", "Onsen", "Nature"],
        "published": "2025-02-22 08:10",
        "focal_point": "center",
        "image": (
            "Mount Yufudake and Yufumi-dori Street in front of Yufuin Station.jpg"
        ),
        "gallery": [
            (
                "Stream near Tenso Shrine and Lake Kinrinko.JPG",
                "The stream that feeds Lake Kinrin.",
            ),
            ("Yufudake-2.jpg", "Mount Yufu, with its two peaks."),
            (
                "Forest of Quercus serrata and Chagall Museum on side of Lake Kinrinko.JPG",
                "The quiet side of the lake.",
            ),
        ],
        "content": """\
Yufuin is only about an hour from Oita, so I went for the day. I took an early
train on purpose. Everybody told me the same thing: come before ten, or you
will spend the day walking behind a tour group.

They were right.

## The main street

When you leave the station, there is one long road called Yunotsubo Kaido that
leads towards the lake. It takes about 20 minutes to walk. On both sides there
are small shops selling cheese cake, croquettes, honey and roasted chestnuts.

At eight in the morning most of them were still closed and the road was almost
empty. Mount Yufu stood straight ahead with snow on both peaks. I stopped
several times just to look at it.

## Lake Kinrin

The lake at the end of the road is small. You can walk around it in fifteen
minutes. What makes it special is that hot spring water and cold spring water
both flow into it, so on a cold morning the surface steams.

I sat on a bench with a coffee and watched the mist move across the water. A
few ducks. One old man taking photographs. That was all. By the time I walked
back, the street was full.

## Food

I ate a croquette made with Bungo beef from a stall near the middle of the
road, 300 yen. Later I had a *toriten* set — Oita-style chicken tempura — for
lunch. Toriten is the food of my prefecture and I still think it is better
than normal fried chicken.

## Would I go again

Yes, but next time I want to stay one night. The day trippers all leave on the
late afternoon train, and people say the town becomes very quiet again after
that. I want to see it.

## Getting there

The local train from Oita takes about an hour and costs 1,130 yen. There is
also a famous sightseeing train called the Yufuin no Mori from Hakata, but you
need to book it early.
""",
    },
    {
        "slug": "plum-trees-and-old-prayers-at-dazaifu",
        "title": "Plum Trees and Old Prayers at Dazaifu",
        "excerpt": (
            "A shrine near Fukuoka where students come to pray before exams, "
            "and 6,000 plum trees flower in early spring."
        ),
        "tags": ["Fukuoka", "History"],
        "published": "2025-03-08 11:45",
        "focal_point": "center",
        "image": "20100719 Dazaifu Tenmangu Shrine 3328.jpg",
        "gallery": [
            (
                "Dazaifu Tenmangu Plum Tree 2004-03-07.jpg",
                "Plum blossom in early March.",
            ),
            (
                "Dazaifu Tenmangu Shrine Honden (Main Prayer Hall).jpg",
                "The main hall, where people leave their wishes.",
            ),
        ],
        "content": """\
Dazaifu Tenmangu is about 30 minutes from Fukuoka city. It is dedicated to
Sugawara no Michizane, a scholar and government official who was sent away
from the capital about 1,100 years ago and died here.

Because he was a great scholar, people now come to pray for success in study.
In February and March the shrine is full of students before their exams.

## The plum trees

Michizane loved plum blossom. There are now around 6,000 plum trees in the
grounds. I went in the first week of March and most of them were open — white
and light pink, and the smell is much stronger than cherry blossom.

There is one tree in front of the main hall called *Tobiume*, the "flying plum
tree". The story says it flew from Kyoto to Dazaifu to follow him. It is
always the first tree in the grounds to flower.

## The path to the shrine

From the station to the shrine is a short street full of shops. Almost all of
them sell the same thing: *umegae mochi*, a small round rice cake with red
bean inside, grilled until the outside is crisp. They cost 130 yen and are
best eaten immediately, while still hot. I ate two.

## Something I did not expect

Behind the shrine there is a very modern Starbucks designed by the architect
Kengo Kuma. The whole front is built from thousands of thin wooden sticks
crossing each other. It looks strange next to an old shrine, but somehow it
works.

## A note on writing your wish

You buy a small wooden board called an *ema* for 500 yen, write your wish, and
hang it up. I read a few while I was there. Most were about university
entrance exams. One said only "please let my mother get better".

## Getting there

Take the Nishitetsu line from Fukuoka (Tenjin) and change at Futsukaichi. It
takes about 30 minutes and costs 420 yen.
""",
    },
    {
        "slug": "kumamoto-castle-standing-again",
        "title": "Kumamoto Castle, Standing Again",
        "excerpt": (
            "One of Japan's great castles, badly damaged by an earthquake in "
            "2016 and slowly being rebuilt stone by stone."
        ),
        "tags": ["Kumamoto", "History"],
        "published": "2025-04-05 13:30",
        "focal_point": "center",
        "image": "Kumamoto Castle 04n4272.jpg",
        "gallery": [
            ("Kumamoto Castle 06s5s4272.jpg", "The keep, black against the sky."),
            (
                "Kumamoto Castle 02n3200.jpg",
                "The curved stone base, called musha-gaeshi.",
            ),
        ],
        "content": """\
Kumamoto Castle is black. Most Japanese castles you see in photographs are
white, so the first sight of this one is a surprise. It was built in 1607 by
Kato Kiyomasa, a general who was famous for building things that were very
hard to attack.

## The walls

The stone walls are the part people talk about most. They start almost gently
at the bottom and then curve up until they are nearly vertical at the top.
This shape is called *musha-gaeshi*, which means something like "sends the
warrior back". The idea is that a person can begin to climb, but cannot
finish.

Standing at the bottom and looking up, it is easy to believe.

## The earthquake

In April 2016 two large earthquakes hit Kumamoto. Around 30 percent of the
castle's stone walls collapsed. Roof tiles fell. One small turret survived
standing on a single narrow line of stones, and the photograph of it was in
newspapers all over Japan.

The repair work is still going on and will take until the 2050s. Every stone
that fell is being numbered, cleaned and put back in the same place. When I
visited, there were still rows of numbered stones lying on the ground in the
park.

## What you can see now

The main keep reopened in 2021 and you can go inside and up to the top floor.
There is also a raised walkway that takes you over the construction area, so
you can look down at the broken walls and the work happening below.

Honestly, that walkway was the most interesting part for me. A finished castle
is a nice photograph. A castle being put back together, slowly, by hand, is a
better story.

## Food

Kumamoto is known for *basashi*, raw horse meat. I tried it. It is softer than
I expected and does not taste strong. I am glad I tried it once. I am not sure
I will order it again.

## Getting there

From Kumamoto Station take the tram towards Kengunmachi and get off at
Kumamotojo-mae. About 15 minutes, 180 yen. Entry to the castle is 800 yen.
""",
    },
    {
        "slug": "rowing-a-boat-through-takachiho-gorge",
        "title": "Rowing a Boat Through Takachiho Gorge",
        "excerpt": (
            "Thirty minutes in a small blue boat between cliffs of old lava, "
            "under a waterfall."
        ),
        "tags": ["Miyazaki", "Nature"],
        "published": "2025-05-17 10:00",
        "focal_point": "center",
        "image": "Manai Falls at Takachiho Gorge.jpg",
        "gallery": [
            ("Takachiho Gorge by boat.jpg", "The rowing boats, waiting their turn."),
            (
                "Takachiho Gorge - May 5, 2015.jpg",
                "Looking down into the gorge from the path.",
            ),
        ],
        "content": """\
Takachiho is not easy to reach. There is no train any more — the line closed
years ago — so you have to take a bus, and from Oita it took me most of the
morning. I still think it was worth it.

## What the gorge is

A long time ago, Mount Aso erupted and hot lava flowed into this valley. The
river then cut through the cooled rock. The result is a narrow gorge with tall
cliffs on both sides, and the rock has straight vertical lines in it, like
somebody pressed it into shape.

In the middle, the Manai Falls drops about 17 metres straight into the water.

## The boat

You can rent a small rowing boat for 30 minutes. It costs 4,100 yen for the
boat, and up to three people can sit in it. You row it yourself.

I should say clearly: I am not good at rowing. My first five minutes were
spent turning in a circle while other boats went past me. After that it became
easier, and I got close enough to the waterfall that water landed on my
shoulder.

Book online before you go. When I arrived, the same-day tickets were already
finished for the afternoon.

## The walking path

If you do not want to row, there is a path along the top of the gorge, about
one kilometre long, and it is free. You look down at the boats from above. In
some ways the view is better from up there.

## The old story

Takachiho is also important in Japanese mythology. The story says the sun
goddess Amaterasu hid in a cave here and the world went dark, until the other
gods made her curious enough to come out. There is a shrine, Amano Iwato, that
marks the place. In the evening, Takachiho Shrine performs a short version of
the *kagura* dance that tells this story. It costs 1,000 yen and lasts about
an hour.

## Getting there

Buses run from Kumamoto and from Nobeoka. Plan a full day, or stay one night.
Do not plan to arrive and leave in the same afternoon.
""",
    },
    {
        "slug": "the-wide-open-grass-of-mount-aso",
        "title": "The Wide Open Grass of Mount Aso",
        "excerpt": (
            "One of the largest volcanic craters in the world, with horses "
            "grazing inside it."
        ),
        "tags": ["Kumamoto", "Nature", "Hiking"],
        "published": "2025-06-14 09:40",
        "focal_point": "center",
        "image": "Aso Kusasenri horses (52133462269).jpg",
        "gallery": [
            ("Mount Nakadake, Aso-san.jpg", "The active crater at Nakadake."),
            (
                "MountAsoCrater from Kusasenri viewpoint.jpg",
                "The view from the Kusasenri grass plain.",
            ),
        ],
        "content": """\
Mount Aso is not one mountain. It is a huge old crater, about 25 kilometres
across, with five peaks inside it and towns, rice fields, roads and railway
lines on the flat ground in between. Around 50,000 people live inside the
crater.

When the bus came over the edge and started going down, I understood the size
for the first time. It does not look like a volcano. It looks like a country.

## Kusasenri

Kusasenri is a wide grass plain with a small lake in the middle. Horses graze
there and you can ride one for about 1,500 yen. I did not ride. I sat on the
grass for an hour and watched the clouds move over the hills, which was
exactly what I needed after a working week.

Bring a jacket. Even in June the wind up there was cold.

## The active crater

Nakadake is still active. When the gas level is safe, you can go up to the rim
by road and look down into it — grey rock, a green-blue pool, and white smoke
coming out constantly.

When the gas level is too high, the road closes. This can happen with very
little warning, and it happened while I was there. So I saw the crater from
Kusasenri instead, from a few kilometres away.

**Check the volcano status on the morning you go.** The Aso city website posts
the level every day. If it says level 2 or higher, the crater road will
probably be closed and you should plan something else.

## What I did instead

I went to the Aso Volcano Museum, which was more interesting than I expected —
there are live cameras pointing into the crater — and then to a small
restaurant for *akaushi* beef, the red-brown cattle raised on these hills. A
rice bowl with it cost 1,800 yen and was one of the best meals I have eaten in
Japan.

## Getting there

Take the train to Aso Station on the Hohi line, then the bus up the mountain.
From Oita it is about two and a half hours by train.
""",
    },
    {
        "slug": "dinner-at-a-yatai-in-fukuoka",
        "title": "Dinner at a Yatai in Fukuoka",
        "excerpt": (
            "Eating at a small street stall by the river, on a plastic stool, "
            "next to strangers."
        ),
        "tags": ["Fukuoka", "Food"],
        "published": "2025-07-19 20:15",
        "focal_point": "center",
        "image": "Yatai beside Naka-gawa, Fukuoka, Japan - 20110525-01.jpg",
        "gallery": [
            (
                "Yatai selling ramen beside Naka-gawa, Fukuoka, Japan - 20110525.jpg",
                "A ramen yatai getting ready.",
            ),
            (
                "Skewers of meat at a yatai beside Naka-gawa, Fukuoka, Japan - 20110525.jpg",
                "Yakitori on the grill.",
            ),
            (
                "Fukuhaku Deai Bridge Nakasu Hakata-ku Nishi-nakasu Hakata-ku Fukuoka City 20221129.jpg",
                "The Naka river at Nakasu, where most of the stalls are.",
            ),
        ],
        "content": """\
A *yatai* is a small food stall on wheels. The owner pushes it into place in
the early evening, puts up a cloth roof, sets out about eight stools, and
cooks until late. In the morning it is gone and the pavement is empty again.

Fukuoka has more than 100 of them — more than the rest of Japan together.
Nakasu, an island in the middle of the river, has the largest group.

## Sitting down

This was the part I was nervous about. You cannot see inside from the street,
the seats are close together, and there is no menu outside.

It turned out to be simple. You look for a stall with one free seat, you say
*sumimasen*, and the owner points at the stool. That is all. Nobody minds that
your Japanese is not perfect.

## What I ate

- **Tonkotsu ramen** — the Hakata style, made from pork bone, white and rich.
  The noodles are thin and straight. 700 yen.
- **Yakitori** — grilled chicken on sticks, 150 yen each.
- **Mentaiko tamagoyaki** — rolled omelette with spicy cod roe inside. 600
  yen. This was the best thing on the table.
- One beer, 500 yen.

If you finish your ramen and want more noodles, you can say *kaedama* and they
give you a second portion for about 150 yen. You keep the soup.

## The people

I sat between a man who worked at a bank and had clearly not gone home yet,
and a couple visiting from Osaka. Within ten minutes we were all talking. The
owner joined in while cooking. Nobody exchanged contact details and nobody
expected to. It was just an hour of easy conversation with people I will never
see again.

That is the real reason to eat at a yatai. The food is good, but you can get
good ramen in a normal shop. You cannot get this.

## Practical notes

- Stalls open around 6 pm and close around 2 am.
- Most are cash only.
- Expect to pay 2,000 to 3,000 yen per person.
- Some close in bad weather. If it is raining hard, have a second plan.
- There is no toilet. Go before you sit down.

## Getting there

Nakasu-Kawabata Station on the subway. From Hakata Station it is two stops.
""",
    },
    {
        "slug": "a-quiet-day-in-nagasaki",
        "title": "A Quiet Day in Nagasaki",
        "excerpt": (
            "A harbour city with a long foreign history, a painful memory, "
            "and one of the best night views in Japan."
        ),
        "tags": ["Nagasaki", "History"],
        "published": "2025-09-13 10:30",
        "focal_point": "center",
        "image": "Nagasaki City view from Mt Inasa07s.jpg",
        "gallery": [
            # The CC0 shot that ranks first for this statue has it wrapped
            # in maintenance scaffolding; this one shows what the post
            # actually describes.
            (
                "Trip to Nagasaki; October 2008 (06).jpg",
                "The Peace Statue — one hand up, one hand held out flat.",
                "top",
            ),
            (
                "Glover Garden Nagasaki-150821367.jpg",
                "Glover Garden, above the harbour.",
            ),
        ],
        "content": """\
For more than 200 years, when Japan was closed to the outside world, Nagasaki
was the one place where foreign ships could come. Because of that, the city
does not feel like anywhere else in Kyushu. There are churches on the hills,
Chinese temples near the centre, and European houses above the harbour.

I went for two days. This is what I would do again.

## The Peace Park and the museum

On 9 August 1945 an atomic bomb was dropped on this city. About 74,000 people
died.

The Atomic Bomb Museum is not easy to walk through. There is a clock that
stopped at 11:02. There are pieces of wall, a water tank, a school lunch box.
The explanations are calm and short, which somehow makes it harder.

Nearby is the Hypocentre Park, with a simple black stone marking the exact
point below the explosion, and the Peace Park with its large statue: one hand
pointing up at the sky, one hand held out flat.

I stayed about two hours and then sat outside for a while before I could go on
with the day. If you visit Nagasaki, please go. It costs 200 yen.

## Glover Garden

In the afternoon I went to Glover Garden, on the hill above the port. These
are the houses of the foreign traders who lived here in the 1800s, kept as
they were, with gardens and a wide view over the water. Thomas Glover, a
Scottish merchant, built the oldest wooden Western-style house still standing
in Japan.

It is a bright, easy place, and after the morning I was grateful for that.

## Mount Inasa at night

In the evening I took the ropeway up Mount Inasa. From the top you see the
whole city: the harbour, the bridges, and the lights going up all the hills
around the bay. People here call it one of the three best night views in
Japan, and I would not argue.

Go about 30 minutes before sunset so you see it in daylight first, then again
in the dark. The ropeway is 1,250 yen return.

## Food

**Champon** — noodles in a milky pork and seafood soup, with cabbage, pork,
squid and fish cake piled on top. It was invented in this city for Chinese
students who needed a cheap, filling meal. Around 900 yen. Perfect after a
cold evening on the mountain.

## Getting there

From Oita it is a long trip — around four hours by train with a change at
Tosu. From Fukuoka it is about two hours. The city itself is easy: trams go
everywhere and cost 140 yen.
""",
    },
    {
        "slug": "karatsu-castle-and-the-pine-forest-by-the-sea",
        "title": "Karatsu Castle and the Pine Forest by the Sea",
        "excerpt": (
            "A white castle on the water in Saga, and a wall of pine trees "
            "planted 400 years ago to hold back the wind."
        ),
        "tags": ["Saga", "History", "Nature"],
        "published": "2025-10-25 11:00",
        "focal_point": "center",
        # A closer view than the wide bay shots: at card size the castle
        # needs to fill the frame, not sit in it as a distant speck.
        "image": "View of Tenshu of Karatsu Castle from Jonaibashi Bridge.JPG",
        "gallery": [
            (
                "Nijinomatsubara from Hamasaki beach.jpg",
                "The pine forest, curving along the bay.",
            ),
            (
                "View from Tenshu of Karatsu Castle (Nijino Matsubara and Mount Kagamiyama).JPG",
                "Looking down at the coast from the castle tower.",
            ),
        ],
        "content": """\
Saga is the prefecture that visitors to Kyushu usually skip. It sits between
Fukuoka and Nagasaki, and most people pass straight through it on the train. I
did the same for two years. Then I got off at Karatsu, and I was annoyed with
myself for waiting so long.

## The castle

Karatsu Castle stands on a small hill right at the mouth of the river, with
the sea on one side and the town on the other. It is white, and against blue
water on a clear day it looks almost too neat to be real. People here call it
Maizuru-jo, the "dancing crane castle", because of the way the walls spread
out like wings.

The building you see now is a reconstruction from 1966, so the inside is a
museum rather than an old interior. Go for the top floor. From there you can
see the whole bay, the pine forest, and the mountains behind.

There is a lift up the hill for 100 yen, or stairs for free. I took the stairs
going up and regretted it about halfway.

## Nijinomatsubara

Along the bay there is a forest of about one million black pine trees. It runs
for five kilometres and is only a few hundred metres deep, curving with the
beach — the name means "rainbow pine grove".

It was not an accident. The local lord had it planted in the early 1600s to
stop the sea wind and the blowing sand from damaging the rice fields behind
it. Four hundred years later it is still doing that job.

You can walk or cycle through it. The trees are low and twisted from the wind,
and the light comes through in pieces. It was quiet enough that I could hear
the sea without seeing it.

## Pottery

Karatsu is also one of the old pottery towns of Japan. Karatsu ware is plain,
rough and grey-brown, made for daily use rather than decoration. There are
small workshops around the town where you can watch and buy. I bought one
teacup for 2,000 yen and I use it every morning.

## Food

*Ika* — squid — is the local speciality, and here it is served alive and
transparent, sliced very thin. It is expensive, around 3,000 yen. It is also
very fresh, and the legs are taken away and brought back fried.

## Getting there

From Fukuoka take the subway to Meinohama and stay on the same train — it runs
straight through onto the JR Chikuhi line to Karatsu. About 70 minutes, 1,170
yen.
""",
    },
    {
        "slug": "onsen-hopping-in-kurokawa",
        "title": "Onsen Hopping in Kurokawa",
        "excerpt": (
            "A small mountain village where one wooden pass lets you into "
            "three different outdoor baths."
        ),
        "tags": ["Kumamoto", "Onsen"],
        "published": "2025-11-29 14:20",
        "focal_point": "center",
        "image": "Kurokawa-Onsen Light-up.jpg",
        "gallery": [
            (
                "Street in Kurokawa Onsen.jpg",
                "The village street, following the river.",
            ),
            (
                "2014-08-08 Bathing token at Kurokawa Onsen (Kumamoto).jpg",
                "The wooden pass — good for three baths.",
            ),
        ],
        "content": """\
Kurokawa is a village of about 30 small inns in a river valley in the
mountains of Kumamoto. It is not near a train station. You have to want to go
there.

What makes it different is a decision the innkeepers made together many years
ago. Instead of each inn competing with big signs and concrete buildings, they
agreed to treat the whole village as one inn: dark wood, no bright signs, and
trees everywhere. Walking in, it feels older than it is.

## The wooden pass

You buy a round wooden pass called a *nyuto tegata* for 1,500 yen. It lets you
use the outdoor baths of any three inns in the village, even if you are not
staying there. It is valid for six months, so you do not have to use all three
in one day.

Each bath is different. I chose:

1. One built into the rock beside the river, with the water running past just
   below.
2. One inside a small cave, dark and very hot, where I could not see the other
   end.
3. One high on the hill with an open view of the valley.

Between baths you walk through the village in the cold with wet hair, which is
part of the fun.

## In late November

I went at the end of November. The autumn leaves had mostly fallen but the
mountains were still red-brown, and it was cold enough that steam came off my
skin when I got out of the water.

In winter the village lights hundreds of small bamboo lanterns along the river
in the evening. That runs from December to April. I missed it by about two
weeks, which is my own fault for not checking the dates.

## If you have never used an onsen

- Wash and rinse fully at the shower before entering the bath.
- No swimwear.
- The small towel does not go in the water. Put it on your head or on the
  side.
- Tie up long hair.
- Tattoos are still a problem at some inns. Kurokawa is more relaxed than most
  places, but check first if this matters to you.

## Getting there

Buses run from Kumamoto, from Fukuoka (Hakata) and from Aso Station. From
Aso it is about 50 minutes. There is no train. A car is easiest if you have
one.
""",
    },
    {
        "slug": "sakurajima-the-volcano-next-door",
        "title": "Sakurajima, the Volcano Next Door",
        "excerpt": (
            "An active volcano fifteen minutes by ferry from a city of "
            "600,000 people, and it erupts almost every day."
        ),
        "tags": ["Kagoshima", "Nature"],
        "published": "2026-02-14 09:00",
        "focal_point": "center",
        # Not the Sentinel satellite frame that a search for this volcano
        # turns up first: it carries burnt-in caption text and a watermark,
        # and reads as a diagram rather than a place someone stood.
        "image": "Kagoshima City and Mount Sakurajima from Mount Shiroyama 3.JPG",
        "gallery": [
            ("Sakurajima ferry.jpg", "The ferry that runs all day and all night."),
            (
                "Sunrise from Sakurajima, Kagoshima - Jul 29, 2012.jpg",
                "Early morning across the bay.",
            ),
        ],
        "content": """\
From the centre of Kagoshima city you look across the water and there is a
volcano. Not far away — about four kilometres. It is smoking. It smokes most
days, and it has small eruptions hundreds of times a year.

People here live with it completely normally. Weather reports include the ash
direction. Streets have yellow bags for collecting ash. Schools have hard
hats. Nobody looks up.

## The ferry

The ferry from Kagoshima port takes 15 minutes, costs 200 yen, and runs 24
hours a day, every day. You pay when you get off. There is a famous udon shop
on board, and the ferry is short enough that eating a bowl in time is
genuinely a small challenge.

## What you can do on the island

You cannot climb it. Going near the summit is not allowed, for obvious
reasons.

What you can do:

- **Yunohira Observatory** — the highest point visitors can reach, at 373
  metres. From there you look straight up at the peak, and back across the bay
  at the city. This was the best view of the day.
- **Nagisa foot bath** — a free outdoor foot bath 100 metres long, right by
  the sea, heated by the volcano.
- **Buried torii gate** — after the great eruption of 1914, a shrine gate
  three metres tall was left with only the very top showing above the ash. It
  is still there, exactly as it was, and it is the clearest way to understand
  what happened.

There is a sightseeing bus that connects these stops for 500 yen, or a day
pass for 700 yen.

## The 1914 eruption

That eruption was the largest in Japan in the twentieth century. So much lava
came out that it filled the channel on the eastern side and joined the island
to the mainland permanently. Sakurajima is still called an island, but it has
not been one for over a hundred years.

## A small thing I liked

Sakurajima grows the largest radish in the world — *sakurajima daikon* — some
weighing over 30 kilograms. It also grows the smallest mandarin orange in the
world. Both from the same volcanic soil, on the same island. I bought a small
bag of the oranges at the ferry terminal and ate them on the boat back.

## Getting there

Fly or take the shinkansen to Kagoshima-Chuo, then a tram to the port. From
Oita the train takes most of a day, so I flew from Oita airport instead — one
hour.
""",
    },
    {
        "slug": "walking-among-old-trees-on-yakushima",
        "title": "Walking Among Old Trees on Yakushima",
        "excerpt": (
            "An island of rain, moss and cedar trees that were already old "
            "when Rome was young."
        ),
        "tags": ["Kagoshima", "Nature", "Hiking"],
        "published": "2026-05-09 07:30",
        "focal_point": "center",
        "image": "Shiratani Unsui Gorge 18.jpg",
        "gallery": [
            (
                "Shiratani Unsuikyo, Yakushima island (4196057333).jpg",
                "The moss forest at Shiratani Unsuikyo.",
            ),
            ("Shiratani Unsui Gorge 11.jpg", "Rain, rock and cedar."),
        ],
        "content": """\
Yakushima is a round island south of Kagoshima, about two hours by fast ferry.
It is small — you can drive around it in half a day — but the mountains in the
middle rise to almost 2,000 metres, and they catch an enormous amount of rain.

People say it rains 35 days a month here. That is a joke, but not much of one.
It rained on both of my days.

## The old cedars

The island's cedar trees are called *yakusugi*. Because the soil is poor and
thin, they grow extremely slowly, and slow growth makes dense wood that
resists rot. So they live a very long time. The oldest, Jomon Sugi, is at
least 2,000 years old and possibly much older.

Reaching Jomon Sugi is a serious walk: 10 hours there and back, starting
before sunrise, much of it along an old railway line. I did not have the time
or, honestly, the fitness. I will go back for it.

## Shiratani Unsuikyo

Instead I walked in Shiratani Unsuikyo, and I do not feel that I missed out.

This is the forest that inspired the setting of the film *Princess Mononoke*.
Everything is covered in moss — the ground, the rocks, the fallen trees, the
standing trees. The rain makes the green so strong it does not look natural.
Water runs everywhere, in dozens of small streams, and the sound never stops.

There are three marked routes. I took the middle one, about three hours, which
goes up to a viewpoint called Taiko-iwa where the cloud opens and closes over
the valley below. Entry to the area is 1,000 yen.

## What to bring

- **Proper rain gear.** Not an umbrella. A jacket, and trousers too.
- **Shoes with grip.** Wet moss on rock is exactly as slippery as it sounds. I
  fell once.
- **A dry bag** for your phone and camera.
- **Cash.** There are very few ATMs on the island.

## Deer and monkeys

There are more deer and more monkeys on Yakushima than there are people. I met
both on the path. The deer let me walk past at two metres and did not move.
The monkeys sat in the road and made the bus wait.

## Getting there

Fast ferry from Kagoshima port, about two hours, around 9,000 yen each way.
There are also short flights. Book accommodation before you go — the island is
small and fills up.
""",
    },
]
