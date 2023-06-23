<xsl:stylesheet exclude-result-prefixes="opds" version="3.0" xmlns:opds="http://www.w3.org/2005/Atom"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" html-version="5.0" encoding="utf-8" indent="no" doctype-system="about:legacy-compat"/>
    <xsl:output doctype-public="-//W3c//DTD html 4.01//EN"/>
    <xsl:output doctype-system="http://www.w3c.org/tr/html4/strict.dtd"/>
    <xsl:template match="/opds:feed">
        <html lang="en">
            <head>
                <meta charset="utf-8"/>
                <meta content="width=device-width, initial-scale=1" name="viewport"/>
                <meta name="referrer" content="same-origin"/>
                <meta name="robots" content="noindex"/>
                <meta name="description" content="An online newsrack of periodicals for your ereader"/>
                <link rel="icon" type="image/svg+xml" href="favicon.svg"/>
                <title>
                    <xsl:value-of select="opds:title"/>
                </title>
                <link href="opds.css" media="screen" rel="stylesheet" type="text/css"/>
            </head>
            <body>
                <script src="theme.min.js"></script>
                <div class="container">
                    <div class="notice">
                        <p>
                            <b>This page is an OPDS catalog feed.</b>
                            The URL in your browser's address bar can be used with an ereader
                            that supports OPDS. This will allow you to browse and download
                            new periodicals directly from the ereader.
                        </p>
                        <a href="./">Back</a>
                    </div>
                    <h1>
                        <a>
                            <xsl:attribute name="href">
                                <xsl:value-of select="opds:uri"/>
                            </xsl:attribute>
                            <xsl:value-of select="opds:title"/>
                        </a>
                    </h1>
                    <ul class="entries">
                        <xsl:for-each select="opds:entry">
                            <li>
                                <div class="item-header">
                                    <xsl:value-of select="opds:title"/>
                                </div>
                                <div class="item-updated">
                                    <span class="cat">
                                        <xsl:value-of select="opds:category/@label"/>
                                    </span>
                                    Published
                                    <xsl:value-of select="opds:updated"/>
                                </div>
                                <!--
                                Doesn't work in Firefox
                                <xsl:value-of select="opds:content" disable-output-escaping="yes"/>
                                -->
                                <div class="downloads">
                                    <xsl:for-each select="opds:link[@rel='http://opds-spec.org/acquisition']">
                                        <a class="book">
                                            <xsl:attribute name="href">
                                                <xsl:value-of select="@href"/>
                                            </xsl:attribute>
                                            .<xsl:value-of select="substring-after(@href, '.')"/>
                                        </a>
                                    </xsl:for-each>
                                </div>
                            </li>
                        </xsl:for-each>
                    </ul>
                </div>

            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
