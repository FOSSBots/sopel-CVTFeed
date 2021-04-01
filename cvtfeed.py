"""cvtfeed.py - Miraheze CVT Feed Plugin."""

import re
import sys

from sopel import tools
from sopel.config.types import ListAttribute, StaticSection, ValidatedAttribute
from sopel.module import commands, example, require_admin, require_chanmsg, rule

if sys.version_info.major >= 3:
    unicode = str


class CVTFeedSection(StaticSection):
    """Create configuration for Sopel."""

    stringpatterns = ListAttribute('stringpatterns', str)
    regexpatterns = ListAttribute('regexpatterns', str)
    destination_channels = ListAttribute('destination_channels', str)
    feed_account = ValidatedAttribute('feed_account', str)
    feed_channel = ValidatedAttribute('feed_channel', str)


def setup(bot):
    """Set up the config section."""
    bot.config.define_section('cvtfeed', CVTFeedSection)


def configure(config):
    """Set up the configuration options."""
    config.define_section('cvtfeed', CVTFeedSection, validate=False)
    config.cvtfeed.configure_setting('stringpatterns', 'Enter strings to look for in feed items.')
    config.cvtfeed.configure_setting('regexpatterns', 'Enter regex patterns to look for in feed items')
    config.cvtfeed.configure_setting('destination_channels', 'Enter channels where matching feed items should be sent.')
    config.cvtfeed.configure_setting('feed_account', 'Enter the NickServ account name of the bot that posts feed items in the feed channel.')
    config.cvtfeed.configure_setting('feed_channel', 'Enter the feed channel name.')


@rule('.*')
@require_chanmsg
def match_items(bot, trigger):
    """Relay items if they match configured strings or regex patterns."""
    if trigger.account == bot.config.cvtfeed.feed_account and trigger.sender == bot.config.cvtfeed.feed_channel:
        if any(re.match(regex, trigger.group()) for regex in bot.config.cvtfeed.regexpatterns):
            for channel in bot.config.cvtfeed.destination_channels:
                bot.say(trigger.group(), channel)
            return
        elif any(string in trigger.group() for string in bot.config.cvtfeed.stringpatterns):
            for channel in bot.config.cvtfeed.destination_channels:
                bot.say(trigger.group(), channel)
            return
        return
    return


@commands('cvtpattern')
@example('.cvtpattern add/del string (string)')
@example('.cvtpattern add/del regex (regex)')
@example('.cvtpattern list string/regex')
@require_admin('Patterns can only be managed by admins.')
def manage_pattern(bot, trigger):
    """Manage cvt feed patterns."""
    STRINGS = {
        'success_del': 'Successfully deleted pattern: %s',
        'success_add': 'Successfully added pattern: %s',
        'no_string': 'No matching string pattern found for: %s',
        'no_regex': 'No matching regex pattern found for: %s',
        'invalid': 'Invalid format for %s a pattern. Try: .cvtpattern add (string|regex) sopel',
        'invalid_display': 'Invalid input for displaying patterns.',
        'nonelisted': 'No %s listed in the patterns list.',
        'huh': 'I could not figure out what you wanted to do.',
    }

    strings = {tools.Identifier(string) for string in bot.config.cvtfeed.stringpatterns if string != ''}
    regexes = {tools.Identifier(regex) for regex in bot.config.cvtfeed.regexpatterns if regex != ''}
    text = trigger.group().split()

    if len(text) == 3 and text[1] == 'list':
        if text[2] == 'string':
            if len(strings) > 0:
                patterns = ', '.join(unicode(string) for string in strings)
                bot.say(f'Patterns: {patterns}')
            else:
                bot.reply(STRINGS['nonelisted'] % ('strings'))
        elif text[2] == 'regex':
            if len(regexes) > 0:
                patterns = ', '.join(unicode(regex) for regex in regexes)
                bot.say(f'Patterns: {patterns}')
            else:
                bot.reply(STRINGS['nonelisted'] % ('regex patterns'))
        else:
            bot.reply(STRINGS['invalid_display'])

    elif len(text) == 4 and text[1] == 'add':
        if text[2] == 'regex':
            regexes.add(text[3])
            bot.config.cvtfeed.regexpatterns = regexes
            bot.config.save()
        elif text[2] == 'string':
            strings.add(text[3])
            bot.config.cvtfeed.stringpatterns = strings
            bot.config.save()
        else:
            bot.reply(STRINGS['invalid'] % ('adding'))
            return

        bot.reply(STRINGS['success_add'] % (text[3]))

    elif len(text) == 4 and text[1] == 'del':
        if text[2] == 'regex':
            if tools.Identifier(text[3]) not in regexes:
                bot.reply(STRINGS['no_regex'] % (text[3]))
                return
            regexes.remove(tools.Identifier(text[3]))
            bot.config.cvtfeed.regexpatterns = [unicode(r) for r in regexes]
            bot.config.save()
            bot.reply(STRINGS['success_del'] % (text[3]))
        elif text[2] == 'string':
            if tools.Identifier(text[3]) not in strings:
                bot.reply(STRINGS['no_string'] % (text[3]))
                return
            strings.remove(tools.Identifier(text[3]))
            bot.config.cvtfeed.stringpatterns = [unicode(s) for s in strings]
            bot.config.save()
            bot.reply(STRINGS['success_del'] % (text[3]))
        else:
            bot.reply(STRINGS['invalid'] % ('deleting'))
            return
    else:
        bot.reply(STRINGS['huh'])


@commands('cvtfeed')
@example('.cvtfeed on/off')
@require_admin('The feed can only be enabled/disabled by admins.')
def manage_channel(bot, trigger):
    """Turn the cvt feed on or off for the current channel."""
    text = trigger.group().split()
    channels = {tools.Identifier(channel) for channel in bot.config.cvtfeed.destination_channels if channel != ''}
    if text[1] == 'on':
        if trigger.sender in bot.config.cvtfeed.destination_channels:
            bot.say('The feed is already enabled for this channel')
        else:
            channels.add(trigger.sender)
            bot.config.cvtfeed.destination_channels = channels
            bot.config.save()
            bot.say('Successfully enabled the feed for this channel')
    elif text[1] == 'off':
        if trigger.sender not in bot.config.cvtfeed.destination_channels:
            bot.say('The feed is already disabled for this channel')
        else:
            channels.remove(tools.Identifier(trigger.sender))
            bot.config.cvtfeed.destination_channels = [unicode(c) for c in channels]
            bot.config.save()
            bot.say('Successfully disabled the feed for this channel')
