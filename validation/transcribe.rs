use app_lib::whisper_engine::WhisperEngine;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    env_logger::init();
    let args: Vec<_> = std::env::args().collect();
    anyhow::ensure!(args.len() == 3, "usage: transcribe MODEL_DIRECTORY AUDIO_F32LE");
    let bytes = std::fs::read(&args[2])?;
    anyhow::ensure!(!bytes.is_empty() && bytes.len() % 4 == 0, "invalid PCM input");
    let audio = bytes.chunks_exact(4)
        .map(|sample| f32::from_le_bytes(sample.try_into().unwrap()))
        .collect();
    let engine = WhisperEngine::new_with_models_dir(Some(args[1].clone().into()))?;
    engine.discover_models().await?;
    engine.load_model("tiny").await?;
    let transcript = engine.transcribe_audio(audio, Some("en".into())).await?;
    println!("{transcript}");
    anyhow::ensure!(transcript.to_lowercase().contains("country"), "JFK sample transcription failed");
    Ok(())
}
