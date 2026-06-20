"""Genereer een WordPress-importbestand (WXR) uit de pagina's.

Importeer het resultaat in WordPress via: Tools → Import → WordPress.
Werkt met elk thema; SEO-titels/-descriptions worden gezet voor zowel
Yoast als RankMath. JSON-LD schema zit in de paginacontent zelf.
"""
from __future__ import annotations

import html
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from .components import css, schema_script
from .pages import Page


def _cdata(text: str) -> str:
    # Sluit eventuele ]]> netjes af zodat de CDATA geldig blijft.
    return "<![CDATA[" + text.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def _item(page: Page, cfg: dict, slug_to_pid: dict[str, int], css_block: str) -> str:
    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d %H:%M:%S")
    link = cfg["business"]["domain"].rstrip("/") + "/" + page.slug + "/"
    parent_id = slug_to_pid.get(page.parent_slug, 0)

    schema = schema_script(*page.schema) if page.schema else ""
    full_body = f'<div class="lm-wrap">{css_block}{schema}{page.body}</div>'

    postmeta = "".join(
        f"<wp:postmeta><wp:meta_key>{_cdata(k)}</wp:meta_key>"
        f"<wp:meta_value>{_cdata(v)}</wp:meta_value></wp:postmeta>"
        for k, v in {
            "_yoast_wpseo_title": page.meta_title,
            "_yoast_wpseo_metadesc": page.meta_description,
            "rank_math_title": page.meta_title,
            "rank_math_description": page.meta_description,
        }.items()
    )

    return f"""
  <item>
    <title>{escape(page.title)}</title>
    <link>{escape(link)}</link>
    <pubDate>{now.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
    <dc:creator>{_cdata('admin')}</dc:creator>
    <guid isPermaLink="false">{escape(cfg['business']['domain'].rstrip('/'))}/?page_id={page.pid}</guid>
    <description></description>
    <content:encoded>{_cdata(full_body)}</content:encoded>
    <excerpt:encoded>{_cdata(page.meta_description)}</excerpt:encoded>
    <wp:post_id>{page.pid}</wp:post_id>
    <wp:post_date>{_cdata(date)}</wp:post_date>
    <wp:post_date_gmt>{_cdata(date)}</wp:post_date_gmt>
    <wp:comment_status>{_cdata('closed')}</wp:comment_status>
    <wp:ping_status>{_cdata('closed')}</wp:ping_status>
    <wp:post_name>{_cdata(page.slug)}</wp:post_name>
    <wp:status>{_cdata('publish')}</wp:status>
    <wp:post_parent>{parent_id}</wp:post_parent>
    <wp:menu_order>{page.menu_order}</wp:menu_order>
    <wp:post_type>{_cdata('page')}</wp:post_type>
    <wp:post_password>{_cdata('')}</wp:post_password>
    <wp:is_sticky>0</wp:is_sticky>
    {postmeta}
  </item>"""


def build_wxr(pages: list[Page], cfg: dict) -> str:
    domain = cfg["business"]["domain"].rstrip("/")
    slug_to_pid = {p.slug: p.pid for p in pages}
    css_block = css(cfg)
    items = "".join(_item(p, cfg, slug_to_pid, css_block) for p in pages)
    title = f"{cfg['business']['name']} — {cfg['product']['noun']} {cfg['product']['verb']}"

    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
  xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:wfw="http://wellformedweb.org/CommentAPI/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:wp="http://wordpress.org/export/1.2/">
<channel>
  <title>{escape(title)}</title>
  <link>{escape(domain)}</link>
  <description>{escape(cfg['brand'].get('tagline',''))}</description>
  <pubDate>{datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
  <language>nl-NL</language>
  <wp:wxr_version>1.2</wp:wxr_version>
  <wp:base_site_url>{escape(domain)}</wp:base_site_url>
  <wp:base_blog_url>{escape(domain)}</wp:base_blog_url>
  <wp:author><wp:author_id>1</wp:author_id><wp:author_login>{_cdata('admin')}</wp:author_login>
    <wp:author_email>{_cdata(cfg['business']['email'])}</wp:author_email>
    <wp:author_display_name>{_cdata(cfg['business']['name'])}</wp:author_display_name>
    <wp:author_first_name>{_cdata('')}</wp:author_first_name><wp:author_last_name>{_cdata('')}</wp:author_last_name></wp:author>
  <generator>leadmachine-siteflow</generator>
{items}
</channel>
</rss>
"""
