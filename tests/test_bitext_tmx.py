"""Tests TMX level 2 (formatting) is supported, and parsed appropriately.

The translate-toolkit library does not support level 2 TMX files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/formats/tmx.html

Support in techiaith.utils.bitext attempts to conform to the standard as per definition
here: https://www.gala-global.org/tmx-14b#ContentMarkup_Level2
"""
import tempfile

import pytest

from techiaith.utils.bitext import to_bitext


TMX_SAMPLE_HEADER = """\
<?xml version="1.0" ?>
<tmx version="1.4">
   <header
      creationtool="ABC"
      creationtoolversion="4"
      datatype="PlainText"
      segtype="sentence"
      adminlang="en-us"
      srclang="en-gb"
      o-tmf="DVMDB">
   </header>
   <body>
      <tu
         tuid="0000003"
         datatype="Text"
         srclang="en-gb">
         <prop type="x-domain">0</prop>
         <prop type="x-project">Testing - Profi</prop>
         <prop type="x-idiom-tm-uda-Project_ID">Blah Blah</prop>
         <prop type="x-filename">someconsultationdoc.pdf</prop>
         <prop type="x-rowid">0000003</prop>
"""

TMX_SAMPLE_FOOTER = '</tu></body></tmx>'



def tmx_sample(xml_text):
    return TMX_SAMPLE_HEADER + xml_text + TMX_SAMPLE_FOOTER


def tmx_test_with_sample(content, *testfn_args, **testfn_kw):
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.tmx') as tf:
        tf.write(content)
        tf.flush()
        check_tmx_level2_support(tf.name, *testfn_args, **testfn_kw)


def check_tmx_level2_support(tmx_path, expected, source_langs=('en', 'cy')):
    sentence_pairs = list(to_bitext(tmx_path, source_langs=source_langs))
    for sentence in sentence_pairs:
        (source, target) = sentence
        assert expected == (source.text, target.text)


def test_translation_direction():
    """Test translation direction indicated by filename/path."""
    content = """\
    <tuv xml:lang="en">
        <seg>Our latest available data is from the 2018/29 season, when overall effectiveness was 44.3% against all laboratory-confirmed influenza.</seg>
      </tuv>
    <tuv xml:lang="cy">
      <seg>Y data diweddaraf sydd ar gael i ni yw data tymor 2018/19, sy’n awgrymu mai 44.3% oedd effeithiolrwydd cyffredinol y brechlyn rhag pob math o’r ffliw gafodd ei gadarnhau gan labordy.</seg>
    </tuv>
    """
    with tempfile.NamedTemporaryFile(mode='w+',
                                     prefix='en-cy_',
                                     suffix='.tmx') as tf:
        tf.write(tmx_sample(content))
        tf.flush()
        check_tmx_level2_support(
            tf.name,
            ('Our latest available data is from the 2018/29 season, when overall effectiveness '
             'was 44.3% against all laboratory-confirmed influenza.',
             "Y data diweddaraf sydd ar gael i ni yw data tymor 2018/19, "
             "sy'n awgrymu mai 44.3% oedd effeithiolrwydd cyffredinol "
             "y brechlyn rhag pob math o'r ffliw gafodd ei gadarnhau gan labordy."),
            source_langs=('en', 'cy'))


def test_mislabelled_tmx():
    content = """\
    <tuv xml:lang="en">
        <seg>Our latest available data is from the 2018/29 season, when overall effectiveness was 44.3% against all laboratory-confirmed influenza.</seg>
      </tuv>
    <tuv xml:lang="de">
      <seg>Y data diweddaraf sydd ar gael i ni yw data tymor 2018/19, sy’n awgrymu mai 44.3% oedd effeithiolrwydd cyffredinol y brechlyn rhag pob math o’r ffliw gafodd ei gadarnhau gan labordy.</seg>
    </tuv>
    """
    with tempfile.NamedTemporaryFile(mode='w+',
                                     prefix='en-cy_',
                                     suffix='.tmx') as tf:
        tf.write(tmx_sample(content))
        tf.flush()
        # target language labelled as German (de), but filename labelled as Welsh (cy)
        with pytest.raises(ValueError):
            check_tmx_level2_support(tf.name, (None, None))


def test_no_langs_in_filenmae_and_no_source_langs_given():
    """Filename must contain language pair (e.g en-cy) or source_langs passed to `to_bitext()`."""
    content = """\
    <tuv xml:lang="en">
        <seg>Our latest available data is from the 2018/29 season, when overall effectiveness was 44.3% against all laboratory-confirmed influenza.</seg>
      </tuv>
    <tuv xml:lang="cy">
      <seg>Y data diweddaraf sydd ar gael i ni yw data tymor 2018/19, sy’n awgrymu mai 44.3% oedd effeithiolrwydd cyffredinol y brechlyn rhag pob math o’r ffliw gafodd ei gadarnhau gan labordy.</seg>
    </tuv>
    """
    with tempfile.NamedTemporaryFile(mode='w+',
                                     suffix='.tmx') as tf:
        tf.write(tmx_sample(content))
        tf.flush()
        with pytest.raises(ValueError):
            check_tmx_level2_support(tf.name, ('EN', 'CY'), source_langs=None)


def test_tmx_level2_level1_bwcompat():
    """Test adding level2 support does not break level 1 (plain text/strings)."""
    s = tmx_sample("""\
    <tuv xml:lang="en">
        <seg>Our latest available data is from the 2018/29 season, when overall effectiveness was 44.3% against all laboratory-confirmed influenza.</seg>
      </tuv>
    <tuv xml:lang="cy">
      <seg>Y data diweddaraf sydd ar gael i ni yw data tymor 2018/19, sy’n awgrymu mai 44.3% oedd effeithiolrwydd cyffredinol y brechlyn rhag pob math o’r ffliw gafodd ei gadarnhau gan labordy.</seg>
    </tuv>
    """)
    tmx_test_with_sample(
        s,
        ('Our latest available data is from the 2018/29 season, '
         'when overall effectiveness was 44.3% against all '
         'laboratory-confirmed influenza.',
         "Y data diweddaraf sydd ar gael i ni yw data tymor 2018/19, "
         "sy'n awgrymu mai 44.3% oedd effeithiolrwydd cyffredinol y "
         "brechlyn rhag pob math o'r ffliw gafodd ei gadarnhau gan labordy."))


def test_tmx_level2_bpt():
    """Check that bpt constructs are handled."""
    s = tmx_sample("""
    <tuv xml:lang="en">
      <seg><bpt i="1000001" x="1000001" type="formatting">{b&gt;</bpt>
    Staff-Side Partnership Working<ept i="1000001">&lt;b}</ept></seg>
    </tuv>
    <tuv xml:lang="cy">
      <seg>
        <bpt i="1000001" x="1000001" type="formatting">{b&gt;</bpt>Gweithio mewn Partneriaeth ag Ochr y Staff<ept i="1000001">&lt;b}</ept>
      </seg>
    </tuv>
    """)
    tmx_test_with_sample(
        s,
        ('Staff-Side Partnership Working',
         'Gweithio mewn Partneriaeth ag Ochr y Staff'))


def test_tmx_level2_bpt_ept():
    """Check bpt followed by ept constructs are handled."""
    s = tmx_sample("""\
    <tuv xml:lang="en">
      <seg>
        <bpt i="1000001" x="1000001" type="formatting">{b&gt;</bpt>Tuesday 16<ept i="1000001">&lt;b}</ept><bpt i="1000002" x="1000002" type="formatting">{b^&gt;</bpt>th<ept i="1000002">&lt;b^}</ept><bpt i="1000003" x="1000003" type="formatting">{b&gt;</bpt> May<ept i="1000003">&lt;b}</ept>
      </seg>
   </tuv>
   <tuv xml:lang="cy">
     <seg>
       <bpt i="1000001" x="1000001" type="formatting">{b&gt;</bpt>Dydd Mawrth 16eg o Fai<ept i="1000001">&lt;b}</ept>
    </seg>
   </tuv>
    """)
    tmx_test_with_sample(
        s,
        ('Tuesday 16th May',
         'Dydd Mawrth 16eg o Fai'))


def test_tmx_level2_ph():
    """Check ph constructs are handled."""
    s = tmx_sample("""\
      <tuv xml:lang="en">
        <seg>Healthcare science in Wales:<ph type="join">{j}</ph>Looking Forward.</seg>
      </tuv>
      <tuv xml:lang="cy">
        <seg>Gwyddor Gofal Iechyd yn GIG Cymru:<ph type="join">{j}</ph>Edrych tuag at y Dyfodol.</seg>
      </tuv>
    """)
    tmx_test_with_sample(
        s,
        ('Healthcare science in Wales: Looking Forward.',
         'Gwyddor Gofal Iechyd yn GIG Cymru: Edrych tuag at y Dyfodol.'))


def test_tmx_level2_it():
    """Check italics."""
    s = tmx_sample("""\
    <tuv xml:lang="en">
        <seg><bpt i="1000001" x="1000001" type="formatting">{i&gt;</bpt>Remembering what has happened to women, babies and their families is crucial in helping us to improve our Maternity and Neonatal Services.<ept i="1000001">&lt;i}</ept></seg>
      </tuv>
      <tuv xml:lang="cy">
        <seg><bpt i="1000001" x="1000001" type="formatting">{i&gt;</bpt>Mae cofio beth sydd wedi digwydd i fenywod, babanod a’u teuluoedd yn hanfodol er mwyn ein helpu ni i wella ein Gwasanaethau Mamolaeth a Newyddenedigol.<ept i="1000001">&lt;i}</ept></seg>
      </tuv>
    """)
    tmx_test_with_sample(
        s,
        ('Remembering what has happened to women, babies and their families is crucial in helping us to improve our Maternity and Neonatal Services.',
         "Mae cofio beth sydd wedi digwydd i fenywod, babanod a'u teuluoedd yn hanfodol er mwyn ein helpu ni i wella ein Gwasanaethau Mamolaeth a Newyddenedigol."))
