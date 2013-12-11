$(function(){
	String.prototype.htmlEncode = function(){
		var htmlEscapes = {
		  '&': '&amp;',
		  '<': '&lt;',
		  '>': '&gt;',
		  '"': '&quot;',
		  "'": '&#x27;',
		  '/': '&#x2F;'
		};
		var htmlEscaper = /[&<>"'\/]/g;
		return this.replace(htmlEscaper, function(match){return htmlEscapes[match]});
	};
});
(function($){
	$.fn.comunica = function(options){
		var settings = $.extend({height: 380,width: 310}, options)
		if(settings.width < 310){
			settings.width = 310;
		}
		if(settings.height < 380){
			settings.height = 380;
		}
		this.html($('<div class="comunica"></div>').css({
				display: 'block', 
				height: settings.height - 8 + 'px', 
				width: settings.width - 8 + 'px'
			}).append($('<div id="comunica-chat-pane"></div>').css({
				width: '100%',
				height: settings.height - 118 + 'px',
				'overflow-y': 'auto',
				'overflow-x': 'wrap',
				'word-wrap': 'break-word'
			})).append($('<div class="comunica-controls"></div>').css({
				width: settings.width - 16 + 'px',
				height: '110px'
			}).append($('<textarea class="comunica-msg-input" id="comunica-message-input"></textarea>').css({
				height: '60px',
				width: '100%'
			})).append($('<a href="#" class="comunica-send-btn" id="comunica-send-message">Send</a>'))
				.append($('<button class="comunica-control-button" id="comunica-viewers"><span class="glyphicon glyphicon-list"></span></button>'))
				.append($('<button class="comunica-control-button" id="comunica-settings"><span class="glyphicon glyphicon-cog"></span></button>'))
			)
			.append($('<div class="comunica-drop-menu" id="comunica-settings-drop"><div class="loading"></div></div>'))
			.append($('<div class="comunica-drop-menu" id="comunica-viewers-drop"></div>')
				.append($('<h2>Viewers</h2>'))
				.append($('<div class="loading" id="comunica-viewers-list"></div>'))
			)
			.append($('<div class="comunica-opaque-popup" id="comunica-pick-nickname-popup"></div>')
				.append($('<div class="comunica-pick-nick"></div>')
					.append($('<center></center>')
						.append($('<h3>Pick a name</h3>'))
						.append($('<input type="text" id="comunica-pick-nickname-input">'))
						.append($('<br><button id="comunica-save-nick">Save</button>'))
					)
				)
			)
		);
		$('#comunica-message-input').keydown($.fn.comunica.inputKeyDown);
		$('#comunica-message-input').focus($.fn.comunica.inputFocus);
		$('#comunica-send-message').click($.fn.comunica.sendClick);
		$('#comunica-settings').click($.fn.comunica.settingsClick);
		$('#comunica-viewers').click($.fn.comunica.viewersClick);
		$('#comunica-save-nick').click($.fn.comunica.saveNickClick);
		$('#comunica-pick-nickname-input').keydown(function(event){
			if(event.which == 13){
				event.preventDefault();
				$('#comunica-save-nick').click();
			}
		});
		this.comunica.nick = false;
	}
	$.fn.comunica.connect = function(host, room){
		if('MozWebSocket' in window)
		{
			WebSocket = MozWebSocket;
		}
		if('WebSocket' in window)
		{
			var ws_con = "ws://"+host+"/"+room;
			var ws = new WebSocket(ws_con);
			ws.onopen = this.connected;
			ws.onmessage = this.recvmsg;
			ws.onclose = this.connection_closed;
			this.ws = ws;
		}
	}
	$.fn.comunica.send = function(msg){
		try 
		{
			this.ws.send(msg);
		} 
		catch(ex)
		{
			return false;
		}
	}
	$.fn.comunica.recvmsg = function(event){
		try{
			var json = JSON.parse(event.data);
		} catch (e) {
			console.log("Error parsing frame data: " + event.data);
			return;
		}
		console.log(json);
		if(json.evt == "message"){
			$('#comunica-chat-pane').append('<p style="margin:0;"><span style="color:'+ json.from[1].htmlEncode()
									+ '">' + json.from[0].htmlEncode() + '</span>: ' + json.value.htmlEncode() + '</p>');
			$('#comunica-chat-pane').animate({scrollTop: $('#comunica-chat-pane')[0].scrollHeight}, 300);
		}
		else if(json.evt == "viewers"){
			var viewerList = $('<div class="comunica-viewer-list" id="comunica-viewers-list"></div>');
			json.value.forEach(function(name){
				if(name != null){
					viewerList.append('<p class="comunica-viewer">' + name + '</p>');
				}
			});
			$('#comunica-viewers-drop > #comunica-viewers-list').replaceWith(viewerList)
		}
	}
	$.fn.comunica.inputKeyDown = function(event){
		if(event.which == 13){
			event.preventDefault();
			$('#comunica-send-message').click();
		}
	}
	$.fn.comunica.inputFocus = function(event){
		if(!$(this).comunica.nick){
			event.preventDefault();
			$('#comunica-pick-nickname-popup').show();
			$('#comunica-pick-nickname-input').focus();
			return;
		}
	}
	$.fn.comunica.sendClick = function(event){
		if(!$(this).comunica.nick){
			$('#comunica-pick-nickname-popup').show();
			return;
		}
		event.preventDefault();
		var input = $('#comunica-message-input');
		var msg = input.val();
		if(!msg){return;}
		$(this).comunica.send(JSON.stringify({evt: 'message', value: msg}));
		input.val('');
	}
	$.fn.comunica.connection_closed = function(){
		console.log("WebSocket closed");
	}
	$.fn.comunica.connected = function(){
		console.log("WebSocket opened");
	}
	$.fn.comunica.settingsClick = function(){
		var btnoff = $('#comunica-settings').offset();
		$('#comunica-viewers-drop').hide();
		$('#comunica-settings-drop').fadeToggle().offset({top: btnoff.top-340, left: btnoff.left-100});
	}
	$.fn.comunica.viewersClick = function(){
		var btnoff = $('#comunica-viewers').offset();
		$('#comunica-settings-drop').hide();
		$('#comunica-viewers-drop').fadeToggle().offset({top: btnoff.top-340, left: btnoff.left-100});
		$(this).comunica.send(JSON.stringify({'evt': 'get-viewers'}));
	}
	$.fn.comunica.saveNickClick = function(){
		var nick = $('#comunica-pick-nickname-input').val();
		if(!nick){
			alert("Nickname can not be empty");
			return;
		}
		$(this).comunica.send(JSON.stringify({evt: 'set-nick', value: nick}));
		$(this).comunica.nick = nick;
		$('#comunica-pick-nickname-popup').hide();
	}
}(jQuery));